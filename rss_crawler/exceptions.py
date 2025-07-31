class RSSFeedError(Exception):
    """RSS 피드 관련 오류"""
    pass


class RSSProcessingError(Exception):
    """RSS 처리 중 발생하는 오류"""
    pass


class RSSStorageError(Exception):
    """RSS 저장 중 발생하는 오류"""
    pass 