"""
榜单业务逻辑服务 - 集成DAO功能的简化版本
"""

from datetime import date, datetime, time, timedelta
from typing import Any, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session

from app.models import ranking
from ..db.ranking import Ranking, RankingSnapshot
from ...utils import filter_dict, get_model_fields


class RankingService:
    """榜单业务逻辑服务 - 直接操作数据库"""

    # ==================== 爬虫使用的方法 ====================

    def create_or_update_ranking(
            self, db: Session, ranking_data: dict[str, Any]
    ) -> Ranking:
        """
        根据ranking_data中的信息创建或更新榜单。
        :param db:
        :param ranking_data:
        :return:
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

    @staticmethod
    def batch_create_ranking_snapshots(
            db: Session, snapshots: list[dict[str, Any]], batch_id: str = None
    ) -> list[RankingSnapshot]:
        """
        批量创建榜单快照 - 支持batch_id
        
        :param db: 数据库会话
        :param snapshots: 快照数据列表
        :param batch_id: 批次ID，如果不提供则自动生成
        :return: 创建的快照对象列表
        """

        # 为所有快照数据添加batch_id
        for snapshot in snapshots:
            snapshot['batch_id'] = batch_id

        # 过滤数据并创建对象
        filtered_snapshots = [filter_dict(snapshot, RankingSnapshot) for snapshot in snapshots]
        snapshot_objs = [RankingSnapshot(**snapshot) for snapshot in filtered_snapshots]
        db.add_all(snapshot_objs)
        db.commit()
        return snapshot_objs

    # ==================== API使用的方法 ====================

    @staticmethod
    def get_ranking_by_id(db: Session, ranking_id: int) -> Ranking | None:
        """
        根据ID获取榜单

        :param db:
        :param ranking_id:
        :return:
        """
        return db.get(Ranking, ranking_id)

    def get_ranking_detail_by_day(
            self,
            db: Session,
            ranking_id: int,
            target_date: date,
    ) -> Optional[ranking.RankingDetail]:
        """
        获取某一天的榜单详情
        根据ranking_id在RankingSnapshot查询到此表格当天最后一批次的快照，然后再与Ranking中的榜单信息join

        :param db: 数据库会话对象
        :param ranking_id: 榜单内部ID
        :param target_date: 指定日期，如果为None则获取最新数据
        :return: 榜单详情对象或None
        """
        # 1. 获取榜单基础信息
        ranking_basic = db.get(Ranking, ranking_id)
        if not ranking_basic:
            return None

        # 2. 获取指定日期的快照
        snapshots = self.get_snapshots_by_day(db, ranking_id, target_date)

        if not snapshots or not ranking_basic:
            return None

        # 3. 获取书籍详细信息
        books = [ranking.RankingBook.model_validate(s) for s in snapshots]

        # 4. 构造榜单详情响应
        ranking_detail = ranking.RankingDetail(
            id=ranking_basic.id,
            channel_name=ranking_basic.channel_name,
            sub_channel_name=ranking_basic.sub_channel_name,
            page_id=ranking_basic.page_id,
            rank_group_type=ranking_basic.rank_group_type,
            books=books,
            snapshot_time=snapshots[0].snapshot_time,
        )

        return ranking_detail

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
    def get_rankings_by_name_with_pagination(
            db: Session,
            name: str,
            page: int = 1,
            size: int = 20) -> Tuple[List[ranking.RankingBasic], int]:
        """
        通过榜单名称获取榜单列表
        :param db:
        :param name:
        :param page:
        :param size:
        :return:
        """

        name_pattern = f"%{name}%"
        name_condition = or_(
            Ranking.channel_name.like(name_pattern),
            Ranking.sub_channel_name.like(name_pattern)
        )
        query = select(Ranking).where(name_condition)

        # 获取数据
        rankings = db.execute(
            query.order_by(desc(Ranking.created_at)).offset((page - 1) * size).limit(size)
        ).scalars()

        total = db.scalar(select(func.count(Ranking.id)).where(name_condition))
        total_pages = (total + size - 1) // size if total > 0 else 0

        return [ranking.RankingBasic.model_validate(i) for i in rankings], total_pages

    @staticmethod
    def get_ranges_by_page_with_pagination(
            db: Session,
            page_id: str,
            page: int = 1,
            size: int = 20

    ) -> Tuple[List[ranking.RankingBasic], int]:
        """
        根据榜单页面获取榜单列表
        :param db:
        :param page_id:
        :param page:
        :param size:
        :return:
        """
        query = select(Ranking).where(Ranking.page_id == page_id)
        rankings = db.execute(
            query.order_by(desc(Ranking.created_at)).offset((page - 1) * size).limit(size)
        ).scalars()

        total = db.scalar(select(func.count(Ranking.id)).where(Ranking.page_id == page_id))
        total_pages = (total + size - 1) // size if total > 0 else 0

        return [ranking.RankingBasic.model_validate(i) for i in rankings], total_pages

    @staticmethod
    def get_snapshots_by_day(
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
    def get_snapshots_by_hour(
            db: Session, ranking_id: int, target_date: date, target_hour: int
    ) -> list[RankingSnapshot]:
        """
        获取指定日期和小时的榜单快照
        
        :param db: 数据库会话
        :param ranking_id: 榜单ID
        :param target_date: 目标日期
        :param target_hour: 目标小时（0-23）
        :return: 榜单快照列表
        """
        # 构造小时时间范围
        start_time = datetime.combine(target_date, time(target_hour, 0, 0))
        end_time = start_time + timedelta(hours=1)

        # 首先查找目标小时内最新的batch_id
        latest_batch_id = db.scalar(
            select(RankingSnapshot.batch_id)
            .where(
                and_(
                    RankingSnapshot.ranking_id == ranking_id,
                    RankingSnapshot.snapshot_time >= start_time,
                    RankingSnapshot.snapshot_time < end_time,
                )
            )
            .order_by(desc(RankingSnapshot.snapshot_time))
            .limit(1)
        )

        if not latest_batch_id:
            return []

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
        )
        return list(result.scalars())

    def get_ranking_detail_by_hour(
            self,
            db: Session,
            ranking_id: int,
            target_date: date,
            target_hour: int,
    ) -> Optional[ranking.RankingDetail]:
        """
        获取榜单详情，支持精确到小时的查询

        :param db: 数据库会话对象
        :param ranking_id:
        :param target_date: 指定日期
        :param target_hour:
        :return:
        """
        # 1. 获取榜单基础信息
        ranking_basic = db.get(Ranking, ranking_id)
        # 2. 获取快照数据
        snapshots = self.get_snapshots_by_hour(
            db, ranking_id, target_date, target_hour
        )
        if not ranking_basic or not snapshots:
            return None

        # 3. 获取书籍详细信息
        books = [ranking.RankingBook.model_validate(s) for s in snapshots]

        # 4. 构造榜单详情响应
        return ranking.RankingDetail(
            id=ranking_basic.id,
            channel_name=ranking_basic.channel_name,
            sub_channel_name=ranking_basic.sub_channel_name,
            page_id=ranking_basic.page_id,
            rank_group_type=ranking_basic.rank_group_type,
            books=books,
            snapshot_time=snapshots[0].snapshot_time,
        )

    # ==================== 历史数据查询方法 ====================

    def get_ranking_history_by_day(
            self,
            db: Session,
            ranking_id: int,
            start_date: date,
            end_date: date,
    ) -> Optional[ranking.RankingHistory]:
        """
        获取榜单按天的历史数据，每天选择当天最后一次更新的快照

        :param db: 数据库会话对象
        :param ranking_id: 榜单ID
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 榜单历史数据
        """
        # 1. 获取榜单基础信息
        ranking_basic = self.get_ranking_by_id(db, ranking_id)
        if not ranking_basic:
            return None

        # 2. 获取时间范围内每天的最后一次快照
        snapshots = []
        current_date = start_date

        while current_date <= end_date:
            try:
                daily_snapshots = self.get_snapshots_by_day(db, ranking_id, current_date)
                if daily_snapshots:
                    # 构建当天的榜单快照对象
                    books = [ranking.RankingBook.model_validate(s) for s in daily_snapshots]
                    snapshots.append(ranking.RankingSnapshot(
                        books=books,
                        snapshot_time=daily_snapshots[0].snapshot_time,
                    ))
            except ValueError:
                # 如果某天没有数据，跳过
                pass

            current_date += timedelta(days=1)

        # 3. 构造历史数据响应
        return ranking.RankingHistory(
            id=ranking_basic.id,
            channel_name=ranking_basic.channel_name,
            sub_channel_name=ranking_basic.sub_channel_name,
            page_id=ranking_basic.page_id,
            rank_group_type=ranking_basic.rank_group_type,
            snapshots=snapshots,
        )

    def get_ranking_history_by_hour(
            self,
            db: Session,
            ranking_id: int,
            start_time: datetime,
            end_time: datetime,
    ) -> Optional[ranking.RankingHistory]:
        """
        获取榜单按小时的历史数据，每小时选择当小时最后一次更新的快照

        :param db: 数据库会话对象
        :param ranking_id: 榜单ID
        :param start_time: 开始时间（分和秒应为0）
        :param end_time: 结束时间（分和秒应为0）
        :return: 榜单历史数据
        """
        # 1. 获取榜单基础信息
        ranking_basic = self.get_ranking_by_id(db, ranking_id)
        if not ranking_basic:
            return None

        # 2. 获取时间范围内每小时的最后一次快照
        snapshots = []
        current_time = start_time

        while current_time <= end_time:
            try:
                hourly_snapshots = self.get_snapshots_by_hour(
                    db, ranking_id, current_time.date(), current_time.hour
                )
                if hourly_snapshots:
                    # 构建当小时的榜单快照对象
                    books = [ranking.RankingBook.model_validate(s) for s in hourly_snapshots]
                    snapshots.append(ranking.RankingSnapshot(
                        books=books,
                        snapshot_time=hourly_snapshots[0].snapshot_time,
                        novel_id=0,  # 这个字段在这里不适用
                        position=0,  # 这个字段在这里不适用
                    ))
            except (ValueError, IndexError):
                # 如果某小时没有数据，跳过
                pass

            current_time += timedelta(hours=1)

        # 4. 构造历史数据响应
        return ranking.RankingHistory(
            id=ranking_basic.id,
            channel_name=ranking_basic.channel_name,
            sub_channel_name=ranking_basic.sub_channel_name,
            page_id=ranking_basic.page_id,
            rank_group_type=ranking_basic.rank_group_type,
            snapshots=snapshots,
        )
