"""
榜单业务逻辑服务 - 集成DAO功能的简化版本
"""

from datetime import date, datetime, timedelta
from typing import Any, Tuple, List

from fastapi import HTTPException
from sqlalchemy import and_, desc, distinct, func, or_, select, text
from sqlalchemy.orm import Session

from ..db.book import Book
from ..db.ranking import Ranking, RankingSnapshot
from ...utils import filter_dict, get_model_fields
from app.models import ranking


class RankingService:
    """榜单业务逻辑服务 - 直接操作数据库"""

    # ==================== 爬虫使用的方法 ====================

    def create_or_update_ranking(
        self, db: Session, ranking_data: dict[str, Any]
    ) -> Ranking:
        """
        根据ranking_data中的信息创建或更新榜单。
        """
        rank_id = ranking_data.get("rank_id")
        if not rank_id:
            raise ValueError("ranking_data中必须包含rank_id")

        # 1. 根据rank_id查找所有可能的榜单
        candidate_rankings = self.get_rankings_by_rank_id(db, rank_id)
        # 2. 根据查找结果进行逻辑判断
        if not candidate_rankings:
            # 榜单不存在，直接创建
            return self.create_ranking(db, ranking_data)
        elif len(candidate_rankings) == 1:
            # 列表只有一个元素，直接更新
            return self.update_ranking(db, candidate_rankings[0], ranking_data)
        else:
            # 列表有多个元素，channel_id进行二次筛选
            channel_id = ranking_data.get("channel_id")
            if not channel_id:
                raise ValueError(
                    f"rank_id '{rank_id}' 对应多个榜单，必须提供channel_id进行区分"
                )

            # 进行二次筛选
            filtered_rankings = [
                r for r in candidate_rankings if r.channel_id == channel_id
            ]

            if len(filtered_rankings) == 1:
                # 精准匹配到一个，更新它
                return self.update_ranking(db, filtered_rankings[0], ranking_data)
            elif len(filtered_rankings) == 0:
                return self.create_ranking(db, ranking_data)
            else:
                # 理论上不应该发生，除非(rank_id, channel_id)组合在数据库中不唯一
                raise SystemError(
                    f"数据库中存在重复的(rank_id, channel_id)组合: ('{rank_id}', '{channel_id}')"
                )

    def batch_create_ranking_snapshots(
        self, db: Session, snapshots: list[dict[str, Any]], batch_id: str = None
    ) -> list[RankingSnapshot]:
        """
        批量创建榜单快照 - 支持batch_id
        
        :param db: 数据库会话
        :param snapshots: 快照数据列表
        :param batch_id: 批次ID，如果不提供则自动生成
        :return: 创建的快照对象列表
        """
        from ...utils.batch import ensure_batch_id
        
        # 确保有batch_id
        if batch_id is None:
            batch_id = ensure_batch_id()
        
        # 为所有快照数据添加batch_id
        for snapshot in snapshots:
            snapshot['batch_id'] = batch_id
        
        # 过滤数据并创建对象
        valid_fields = get_model_fields(RankingSnapshot)
        filtered_snapshots = [filter_dict(snapshot, valid_fields) for snapshot in snapshots]
        snapshot_objs = [RankingSnapshot(**snapshot) for snapshot in filtered_snapshots]
        db.add_all(snapshot_objs)
        db.commit()
        return snapshot_objs

    # ==================== API使用的方法 ====================

    @staticmethod
    def get_ranking_by_id(db: Session, ranking_id: int) -> Ranking | None:
        """
        根据ID获取榜单

        :param self:
        :param db:
        :param ranking_id:
        :return:
        """
        return db.get(Ranking, ranking_id)


    def get_ranking_statistics(self, db: Session, ranking_id: int) -> dict[str, Any]:
        """获取榜单统计信息"""
        result = db.execute(
            select(
                func.count(distinct(RankingSnapshot.snapshot_time)).label(
                    "total_snapshots"
                ),
                func.count(distinct(RankingSnapshot.novel_id)).label("unique_books"),
                func.min(RankingSnapshot.snapshot_time).label("first_snapshot_time"),
                func.max(RankingSnapshot.snapshot_time).label("last_snapshot_time"),
            ).where(RankingSnapshot.ranking_id == ranking_id)
        ).first()

        if result:
            return {
                "total_snapshots": result.total_snapshots or 0,
                "unique_books": result.unique_books or 0,
                "first_snapshot_time": result.first_snapshot_time,
                "last_snapshot_time": result.last_snapshot_time,
            }
        return {}

    def get_ranking_detail(
        self,
        db: Session,
        ranking_id: int,
        target_date: date | None = None,
        limit: int = 50,
    ) -> dict[str, Any] | None:
        """
        获取榜单详情
        :param db:
        :param ranking_id:
        :param target_date:
        :param limit:
        :return:
        """
        ranking = self.get_ranking_by_id(db, ranking_id)
        if not ranking:
            raise HTTPException(status_code=404, detail="榜单不存在")

        # 获取快照数据
        if target_date:
            snapshots = self.get_snapshots_by_date(
                db, ranking_id, target_date, limit
            )
        else:
            snapshots = self.get_latest_snapshots_by_ranking_id(db, ranking_id, limit)

        # 构造详情数据
        books_data = []
        for snapshot in snapshots:
            # 获取书籍信息
            book = db.get(Book, snapshot.novel_id)
            book_data = {
                "novel_id": snapshot.novel_id,
                "title": book.title if book else "未知书籍",
                "position": snapshot.position,
                "score": snapshot.score,
                "snapshot_time": snapshot.snapshot_time,
            }
            books_data.append(book_data)

        return {
            "ranking": ranking,
            "books": books_data,
            "snapshot_time": snapshots[0].snapshot_time if snapshots else None,
            "total_books": len(books_data),
            "statistics": self.get_ranking_statistics(db, ranking_id),
        }

    def get_ranking_history(
        self,
        db: Session,
        ranking_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """获取榜单历史趋势"""
        start_time = None
        end_time = None

        if start_date:
            start_time = datetime.combine(start_date, datetime.min.time())
        if end_date:
            end_time = datetime.combine(end_date, datetime.max.time())

        trend_data = self.get_ranking_trend(db, ranking_id, start_time, end_time)

        return {
            "ranking_id": ranking_id,
            "start_date": start_date,
            "end_date": end_date,
            "trend_data": [
                {"snapshot_time": snapshot_time, "book_count": book_count}
                for snapshot_time, book_count in trend_data
            ],
        }

    def compare_rankings(
        self, db: Session, ranking_ids: list[int], target_date: date | None = None
    ) -> dict[str, Any]:
        """对比多个榜单"""
        if len(ranking_ids) < 2:
            raise ValueError("至少需要2个榜单进行对比")

        # 获取榜单基本信息
        rankings = [self.get_ranking_by_id(db, rid) for rid in ranking_ids]
        rankings = [r for r in rankings if r is not None]

        if len(rankings) != len(ranking_ids):
            raise ValueError("部分榜单不存在")

        # 获取对比数据
        comparison_data = {}
        for ranking_id in ranking_ids:
            if target_date:
                snapshots = self.get_snapshots_by_date(
                    db, ranking_id, target_date
                )
            else:
                snapshots = self.get_latest_snapshots_by_ranking_id(db, ranking_id)
            comparison_data[ranking_id] = snapshots

        # 分析共同书籍
        all_books = {}  # novel_id -> book_info
        ranking_books = {}  # ranking_id -> set of novel_ids

        for ranking_id, snapshots in comparison_data.items():
            novel_ids = set()
            for snapshot in snapshots:
                novel_ids.add(snapshot.novel_id)
                # 获取书籍信息
                book = db.get(Book, snapshot.novel_id)
                all_books[snapshot.novel_id] = {
                    "id": book.id if book else None,
                    "novel_id": snapshot.novel_id,
                    "title": book.title if book else "未知书籍",
                }
            ranking_books[ranking_id] = novel_ids

        # 找出共同书籍
        common_novel_ids = (
            set.intersection(*ranking_books.values()) if ranking_books else set()
        )

        return {
            "rankings": [
                {"ranking_id": r.id, "name": r.name, "page_id": r.page_id}
                for r in rankings
            ],
            "comparison_date": target_date or date.today(),
            "ranking_data": {
                ranking_id: [
                    {
                        "novel_id": s.novel_id,
                        "title": all_books.get(s.novel_id, {}).get("title", "未知书籍"),
                        "position": s.position,
                        "score": s.score,
                    }
                    for s in snapshots
                ]
                for ranking_id, snapshots in comparison_data.items()
            },
            "common_books": [all_books[novel_id] for novel_id in common_novel_ids],
            "stats": {
                "total_unique_books": len(all_books),
                "common_books_count": len(common_novel_ids),
            },
        }

    def get_book_ranking_history_with_details(
        self,
        db: Session,
        novel_id: int,
        days: int = 30,
    ) -> List[book.BookRankingInfo]:
        """
        获取书籍在days天中的每天的榜单排名历史（取每天中最后一次榜单快照）

        :param db: 数据库会话对象
        :param novel_id: 书籍唯一标识ID
        :param days: 查询天数，默认30天
        :return: BookRankingInfo列表，包含榜单信息和排名快照
        """
        from ..sql.ranking_queries import BOOK_DAILY_LAST_RANKING_HISTORY_QUERY
        
        # 计算开始时间
        start_time = datetime.now() - timedelta(days=days)
        
        # 使用高性能Text查询执行窗口函数
        results = db.execute(
            text(BOOK_DAILY_LAST_RANKING_HISTORY_QUERY),
            {
                "novel_id": novel_id,
                "start_time": start_time
            }
        ).all()
        return [book.BookRankingInfo.model_validate(row._asdict()) for row in results]

    # ==================== 内部依赖方法 ====================
    @staticmethod
    def get_rankings_by_rank_id(db: Session, rank_id: str) -> List[Ranking]:
        """
        根据rank_id获取所有匹配的榜单列表
        :param db:
        :param rank_id:
        :return: 一个榜单对象的列表
        """
        return list(db.execute(select(Ranking).where(Ranking.rank_id == rank_id)).scalars())

    @staticmethod
    def create_ranking(db: Session, ranking_data: dict[str, Any]) -> Ranking:
        """创建榜单"""
        valid_fields = get_model_fields(Ranking)
        filtered_data = filter_dict(ranking_data, valid_fields)
        
        ranking = Ranking(**filtered_data)
        db.add(ranking)
        db.commit()
        db.refresh(ranking)
        return ranking

    @staticmethod
    def update_ranking(db: Session, ranking: Ranking, ranking_data: dict[str, Any]
    ) -> Ranking:
        """更新榜单"""
        valid_fields = get_model_fields(Ranking)
        filtered_data = filter_dict(ranking_data, valid_fields)
        
        for key, value in filtered_data.items():
            if hasattr(ranking, key):
                setattr(ranking, key, value)
        ranking.updated_at = datetime.now()
        db.add(ranking)
        db.commit()
        db.refresh(ranking)
        return ranking

    @staticmethod
    def get_rankings_with_pagination(
        db: Session,
        page: int = 1,
        size: int = 20,
        page_id: str | None = None,
        name: str | None = None,
    ) -> Tuple[List[ranking.RankingBasic], int]:
        """
        分页获取榜单列表
        
        首先根据page_id查找榜单，如果page_id为空或没有查找到就使用name在Ranking
        表格中的channel_name和sub_channel_name中进行模糊匹配。
        
        :param db: 数据库会话对象
        :param page: 页码，从1开始
        :param size: 每页数量，1-100之间
        :param page_id: 榜单页面ID筛选，精确匹配
        :param name: 榜单名称筛选，模糊匹配
        :return: (榜单列表, 总页数)
        """
        skip = (page - 1) * size

        # 构建查询
        query = select(Ranking)
        count_query = select(func.count(Ranking.id))

        # 优先使用page_id精确匹配
        if page_id:
            query = query.where(Ranking.page_id == page_id)
            count_query = count_query.where(Ranking.page_id == page_id)
        elif name:
            # page_id为空或未提供时，使用name在channel_name和sub_channel_name中模糊匹配
            name_pattern = f"%{name}%"
            name_condition = or_(
                Ranking.channel_name.like(name_pattern),
                Ranking.sub_channel_name.like(name_pattern)
            )
            query = query.where(name_condition)
            count_query = count_query.where(name_condition)

        # 获取数据
        rankings = db.execute(
                query.order_by(desc(Ranking.created_at)).offset(skip).limit(size)
            ).scalars()

        total = db.scalar(count_query)
        total_pages = (total + size - 1) // size if total > 0 else 0

        return rankings, total_pages

    def get_latest_snapshots_by_ranking_id(
        self, db: Session, ranking_id: int, limit: int = 50
    ) -> list[RankingSnapshot]:
        """
        获取榜单最新快照 - 使用batch_id确保数据一致性
        
        优先获取最新batch_id的完整数据，确保所有书籍数据来自同一次爬取
        """
        # 获取最新的batch_id
        latest_batch_id = db.scalar(
            select(RankingSnapshot.batch_id)
            .where(RankingSnapshot.ranking_id == ranking_id)
            .order_by(desc(RankingSnapshot.snapshot_time))
            .limit(1)
        )

        if not latest_batch_id:
            return []

        # 使用最新batch_id获取完整的快照数据
        result = db.execute(
            select(RankingSnapshot)
            .where(
                and_(
                    RankingSnapshot.ranking_id == ranking_id,
                    RankingSnapshot.batch_id == latest_batch_id,
                )
            )
            .order_by(RankingSnapshot.position)
            .limit(limit)
        )
        return list(result.scalars())

    @staticmethod
    def get_snapshots_by_date(
        db: Session, ranking_id: int, target_date: date, limit: int = 50
    ) -> list[RankingSnapshot]:
        """
        获取指定日期的榜单快照 - 使用batch_id确保数据一致性
        
        优先使用batch_id来获取一致的批次数据，而不是依赖snapshot_time
        
        :param db: 数据库会话
        :param ranking_id: 榜单ID
        :param target_date: 目标日期
        :param limit: 返回数量限制
        :return: 榜单快照列表
        """
        # 首先查找目标日期最新的batch_id
        latest_batch_id = db.scalar(
            select(RankingSnapshot.batch_id)
            .where(
                and_(
                    RankingSnapshot.ranking_id == ranking_id,
                    func.date(RankingSnapshot.snapshot_time) == target_date,
                )
            )
            .order_by(desc(RankingSnapshot.snapshot_time))
            .limit(1)
        )

        if not latest_batch_id:
            raise ValueError("Don't exist records in target time")

        # 使用batch_id获取同一批次的所有数据，确保时间一致性
        result = db.execute(
            select(RankingSnapshot)
            .where(
                and_(
                    RankingSnapshot.ranking_id == ranking_id,
                    RankingSnapshot.batch_id == latest_batch_id,
                )
            )
            .order_by(RankingSnapshot.position)
            .limit(limit)
        )
        return list(result.scalars())

    @staticmethod
    def get_snapshots_by_batch_id(
        db: Session, ranking_id: int, batch_id: str, limit: int = 50
    ) -> list[RankingSnapshot]:
        """
        根据batch_id获取榜单快照
        
        :param db: 数据库会话
        :param ranking_id: 榜单ID
        :param batch_id: 批次ID
        :param limit: 返回数量限制
        :return: 榜单快照列表
        """
        result = db.execute(
            select(RankingSnapshot)
            .where(
                and_(
                    RankingSnapshot.ranking_id == ranking_id,
                    RankingSnapshot.batch_id == batch_id,
                )
            )
            .order_by(RankingSnapshot.position)
            .limit(limit)
        )
        return list(result.scalars())

    @staticmethod
    def get_available_batch_ids_by_date(
        db: Session, ranking_id: int, target_date: date
    ) -> list[str]:
        """
        获取指定日期的所有可用batch_id
        
        :param db: 数据库会话
        :param ranking_id: 榜单ID
        :param target_date: 目标日期
        :return: batch_id列表
        """
        result = db.execute(
            select(distinct(RankingSnapshot.batch_id))
            .where(
                and_(
                    RankingSnapshot.ranking_id == ranking_id,
                    func.date(RankingSnapshot.snapshot_time) == target_date,
                )
            )
            .order_by(desc(RankingSnapshot.batch_id))
        )
        return [row for row in result.scalars()]

    def get_book_ranking_history(
        self,
        db: Session,
        novel_id: int,
        ranking_id: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 30,
    ) -> list[RankingSnapshot]:
        """获取书籍排名历史"""
        query = select(RankingSnapshot).where(RankingSnapshot.novel_id == novel_id)

        if ranking_id:
            query = query.where(RankingSnapshot.ranking_id == ranking_id)
        if start_time:
            query = query.where(RankingSnapshot.snapshot_time >= start_time)
        if end_time:
            query = query.where(RankingSnapshot.snapshot_time <= end_time)

        result = db.execute(
            query.order_by(desc(RankingSnapshot.snapshot_time)).limit(limit)
        )
        return list(result.scalars())

    def get_ranking_trend(
        self,
        db: Session,
        ranking_id: int,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[tuple[datetime, int]]:
        """获取榜单变化趋势（每个快照时间的书籍数量）"""
        query = select(
            RankingSnapshot.snapshot_time,
            func.count(RankingSnapshot.novel_id).label("book_count"),
        ).where(RankingSnapshot.ranking_id == ranking_id)

        if start_time:
            query = query.where(RankingSnapshot.snapshot_time >= start_time)
        if end_time:
            query = query.where(RankingSnapshot.snapshot_time <= end_time)

        result = db.execute(
            query.group_by(RankingSnapshot.snapshot_time).order_by(
                RankingSnapshot.snapshot_time
            )
        ).all()

        return [(row.snapshot_time, row.book_count) for row in result]
