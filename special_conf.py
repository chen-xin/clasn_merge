import re

# sort proxys by fee rate
def get_order(pattern_str, fn):
    pattern = re.compile(pattern_str)
    def _get_order(s:str):
        p = pattern.search(s)
        if p:
            result = fn(p[0])
            # print('[%s]: %s'%(result, s))
        else:
            result = 9999
        return result

    def sort_proxies(proxies:list):
        proxies.sort(key=_get_order)

    # return sort_proxies
    return _get_order

def filter_warmane(pattern_str):
    pattern = re.compile(pattern_str)
    def _get_warmane_proxies(proxies:list):
        return [x for x in filter(lambda x: pattern.search(x), proxies)]
    return _get_warmane_proxies


provider_confs = {
    '厘米aloy.asia_20220315': {
        'order_fn': get_order(
            '-(\d+\.)?\d+X ',
            lambda x: float(x[1:-2])),
        'warmane_filter': filter_warmane('(香港|狮城)')
    },
    'edu.lovess.top_20251210': {
        'order_fn': get_order(
            '\|\d(\.\d)?:\d(\.\d)?\|',
            lambda x: sum(map(float, x[1:-1].split(':')))),
        'warmane_filter': filter_warmane('🇸🇬 SG')
    },
    'haojiahuo_20220612': {
        'order_fn': lambda x: 1,
        'warmane_filter': filter_warmane('(香港|新加坡|德国)')
    }
}
