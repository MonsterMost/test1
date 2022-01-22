def get_total_pages(count_product, max_quantity):
    pages = count_product // max_quantity
    if count_product % max_quantity !=0:
        pages +=1
    return pages