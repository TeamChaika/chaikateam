def get_pagination(page, pages_count):
    if page < 3:
        return range(1, min(5, pages_count) + 1)
    elif page > pages_count - 2:
        return range(
            max(1, page - (4 - (pages_count - page))), pages_count + 1
        )
    return range(page - 2, page + 3)
