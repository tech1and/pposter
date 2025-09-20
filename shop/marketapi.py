import asyncio
import json
import aiohttp

#from asgiref.sync import sync_to_async
from django.shortcuts import render


from .models import Category

'''
def get_or_create_eventloop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError as ex:
        if "There is no current event loop in thread" in str(ex):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return asyncio.get_event_loop()
'''


async def cats(request, self, **kwargs):
    category = self.kwargs['slug']
    cat = Category.objects.get(slug=category)
    catt_title = cat.title

    headers = {'Authorization': 'DdgkTKcDCK8mDmqwMw34nCxNJhY6Vs'}

    url = f'https://api.content.market.yandex.ru/v3/affiliate/search?text={catt_title}&geo_id=213&clid=2368620&fields=MODEL_PRICE,MODEL_RATING,MODEL_DEFAULT_OFFER,MODEL_MEDIA,OFFER_PHOTO,OFFER_DELIVERY&count=30'

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=4) as response:
            market = await response.text()
            market = json.loads(market)
            market = market['items']

    # return await sync_to_async(render)(
    #    request, 'market.html', {'market': market}
    # )
    return render(request, 'market.html', {'market': market})
loop = asyncio.get_event_loop()
loop.run_until_complete(cats())
