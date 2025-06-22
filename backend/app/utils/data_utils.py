"""
数据处理工具

提供数据验证、转换、清洗等数据相关的工具函数
"""
import re
import html
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


def validate_data(data: Any, rules: Dict[str, Callable]) -> Dict[str, Any]:
    """
    数据验证
    
    Args:
        data: 要验证的数据（字典格式）
        rules: 验证规则字典 {字段名: 验证函数}
        
    Returns:
        Dict[str, Any]: 验证结果 {"valid": bool, "errors": [], "data": {}}
    """
    result = {
        "valid": True,
        "errors": [],
        "data": {}
    }
    
    if not isinstance(data, dict):
        result["valid"] = False
        result["errors"].append("数据必须是字典格式")
        return result
    
    for field, validator in rules.items():
        try:
            if field in data:
                validated_value = validator(data[field])
                result["data"][field] = validated_value
            else:
                result["valid"] = False
                result["errors"].append(f"缺少必需字段: {field}")
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"字段 {field} 验证失败: {str(e)}")
    
    return result


def clean_text(text: str, 
               remove_html: bool = True,
               remove_extra_spaces: bool = True,
               normalize_quotes: bool = True) -> str:
    """
    清洗文本数据
    
    Args:
        text: 原始文本
        remove_html: 是否移除HTML标签
        remove_extra_spaces: 是否移除多余空格
        normalize_quotes: 是否标准化引号
        
    Returns:
        str: 清洗后的文本
    """
    if not isinstance(text, str):
        return str(text)
    
    # 移除HTML实体
    text = html.unescape(text)
    
    # 移除HTML标签
    if remove_html:
        text = re.sub(r'<[^>]+>', '', text)
    
    # 标准化引号
    if normalize_quotes:
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
    
    # 移除多余空格
    if remove_extra_spaces:
        text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def extract_numbers(text: str, number_type: str = "int") -> List[Union[int, float]]:
    """
    从文本中提取数字
    
    Args:
        text: 源文本
        number_type: 数字类型 ("int", "float", "all")
        
    Returns:
        List[Union[int, float]]: 提取到的数字列表
    """
    if number_type == "int":
        # 提取整数
        pattern = r'\b\d+\b'
        matches = re.findall(pattern, text)
        return [int(match) for match in matches]
    
    elif number_type == "float":
        # 提取浮点数
        pattern = r'\b\d+\.\d+\b'
        matches = re.findall(pattern, text)
        return [float(match) for match in matches]
    
    else:  # "all"
        # 提取所有数字
        numbers = []
        
        # 先提取浮点数
        float_pattern = r'\b\d+\.\d+\b'
        float_matches = re.findall(float_pattern, text)
        numbers.extend([float(match) for match in float_matches])
        
        # 移除已匹配的浮点数，然后提取整数
        text_without_floats = re.sub(float_pattern, '', text)
        int_pattern = r'\b\d+\b'
        int_matches = re.findall(int_pattern, text_without_floats)
        numbers.extend([int(match) for match in int_matches])
        
        return numbers


def safe_int(value: Any, default: int = 0) -> int:
    """
    安全地转换为整数
    
    Args:
        value: 要转换的值
        default: 转换失败时的默认值
        
    Returns:
        int: 转换后的整数
    """
    try:
        if isinstance(value, str):
            # 移除非数字字符（保留负号）
            value = re.sub(r'[^\d-]', '', value)
            if not value or value == '-':
                return default
        
        return int(value)
        
    except (ValueError, TypeError):
        logger.debug(f"整数转换失败: {value}, 使用默认值: {default}")
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    安全地转换为浮点数
    
    Args:
        value: 要转换的值
        default: 转换失败时的默认值
        
    Returns:
        float: 转换后的浮点数
    """
    try:
        if isinstance(value, str):
            # 移除非数字字符（保留小数点和负号）
            value = re.sub(r'[^\d.-]', '', value)
            if not value or value in ['-', '.', '-.']:
                return default
        
        return float(value)
        
    except (ValueError, TypeError):
        logger.debug(f"浮点数转换失败: {value}, 使用默认值: {default}")
        return default


def safe_decimal(value: Any, default: Decimal = Decimal('0')) -> Decimal:
    """
    安全地转换为Decimal
    
    Args:
        value: 要转换的值
        default: 转换失败时的默认值
        
    Returns:
        Decimal: 转换后的Decimal
    """
    try:
        if isinstance(value, str):
            # 移除非数字字符（保留小数点和负号）
            value = re.sub(r'[^\d.-]', '', value)
            if not value or value in ['-', '.', '-.']:
                return default
        
        return Decimal(str(value))
        
    except (InvalidOperation, ValueError, TypeError):
        logger.debug(f"Decimal转换失败: {value}, 使用默认值: {default}")
        return default


def normalize_book_id(book_id: Any) -> Optional[str]:
    """
    标准化书籍ID
    
    Args:
        book_id: 原始书籍ID
        
    Returns:
        Optional[str]: 标准化后的书籍ID
    """
    if not book_id:
        return None
    
    # 转换为字符串并移除空格
    book_id = str(book_id).strip()
    
    # 提取数字部分
    match = re.search(r'\d+', book_id)
    if match:
        return match.group()
    
    return None


def parse_numeric_field(data: Any, field_name: str = "unknown") -> Optional[int]:
    """
    从数据中解析数字字段（专为爬虫数据设计）
    
    支持的格式：
    - 纯数字：123, "456"
    - 带单位：1.2万, 3千, "5.6万"
    - 中文数字：一万, 三千 (基础支持)
    
    Args:
        data: 要解析的数据
        field_name: 字段名（用于日志）
        
    Returns:
        Optional[int]: 解析后的数字，失败时返回None
    """
    if data is None:
        return None
    
    # 转换为字符串并清理
    text = str(data).strip()
    if not text:
        return None
    
    try:
        # 移除常见的无用字符
        text = text.replace(',', '').replace('，', '')
        
        # 尝试直接转换为整数
        if text.isdigit():
            return int(text)
        
        # 处理负数
        if text.startswith('-') and text[1:].isdigit():
            return int(text)
        
        # 处理带单位的数字
        import re
        
        # 匹配数字+单位的模式
        pattern = r'([\d.]+)\s*([万千]?)'
        match = re.search(pattern, text)
        
        if match:
            number_str, unit = match.groups()
            try:
                number = float(number_str)
                
                if unit == '万':
                    return int(number * 10000)
                elif unit == '千':
                    return int(number * 1000)
                else:
                    return int(number)
            except ValueError:
                pass
        
        # 处理纯小数
        try:
            return int(float(text))
        except ValueError:
            pass
        
        # 基础中文数字转换
        chinese_map = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '万': 10000, '千': 1000, '百': 100
        }
        
        if all(c in chinese_map or c in '零' for c in text):
            # 简单的中文数字转换（仅支持基本格式）
            if text == '一万':
                return 10000
            elif text == '三千':
                return 3000
            # 可以根据需要扩展更多规则
        
        logger.debug(f"无法解析数字字段 {field_name}: {text}")
        return None
        
    except Exception as e:
        logger.debug(f"解析数字字段 {field_name} 时出错: {text} - {e}")
        return None


def parse_number_with_unit(text: str) -> Optional[int]:
    """
    解析带单位的数字（如"1.2万", "5千"）
    
    Args:
        text: 带单位的数字文本
        
    Returns:
        Optional[int]: 解析后的数字
    """
    try:
        if not text:
            return None
        
        text = str(text).strip()
        
        # 匹配数字和单位
        match = re.match(r'([\d.]+)\s*([万千]?)', text)
        if not match:
            # 尝试直接转换为数字
            return safe_int(text)
        
        number_str, unit = match.groups()
        number = float(number_str)
        
        if unit == '万':
            return int(number * 10000)
        elif unit == '千':
            return int(number * 1000)
        else:
            return int(number)
            
    except Exception as e:
        logger.debug(f"带单位数字解析失败: {text} - {e}")
        return None


def extract_author_id(author_info: Any) -> Optional[str]:
    """
    从作者信息中提取作者ID
    
    Args:
        author_info: 作者信息（可能是URL、字符串等）
        
    Returns:
        Optional[str]: 作者ID
    """
    if not author_info:
        return None
    
    author_info = str(author_info)
    
    # 从URL中提取ID
    match = re.search(r'authorid=(\d+)', author_info)
    if match:
        return match.group(1)
    
    # 从路径中提取ID
    match = re.search(r'/(\d+)/?$', author_info)
    if match:
        return match.group(1)
    
    # 如果是纯数字，直接返回
    if author_info.isdigit():
        return author_info
    
    return None


def split_tags(tags: str, separator: str = ',') -> List[str]:
    """
    分割标签字符串
    
    Args:
        tags: 标签字符串
        separator: 分隔符
        
    Returns:
        List[str]: 标签列表
    """
    if not tags:
        return []
    
    # 分割并清理标签
    tag_list = [tag.strip() for tag in str(tags).split(separator) if tag.strip()]
    
    return tag_list


def join_tags(tags: List[str], separator: str = ',') -> str:
    """
    合并标签列表
    
    Args:
        tags: 标签列表
        separator: 分隔符
        
    Returns:
        str: 标签字符串
    """
    if not tags:
        return ""
    
    # 清理并合并标签
    clean_tags = [str(tag).strip() for tag in tags if str(tag).strip()]
    
    return separator.join(clean_tags)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        str: 截断后的文本
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def mask_sensitive_data(data: str, mask_char: str = "*", show_prefix: int = 2, show_suffix: int = 2) -> str:
    """
    遮蔽敏感数据
    
    Args:
        data: 敏感数据
        mask_char: 遮蔽字符
        show_prefix: 显示前缀字符数
        show_suffix: 显示后缀字符数
        
    Returns:
        str: 遮蔽后的数据
    """
    if not data or len(data) <= show_prefix + show_suffix:
        return mask_char * len(data) if data else ""
    
    prefix = data[:show_prefix]
    suffix = data[-show_suffix:] if show_suffix > 0 else ""
    mask_length = len(data) - show_prefix - show_suffix
    
    return prefix + mask_char * mask_length + suffix