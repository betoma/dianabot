import aiohttp

class AsyncPastebin: #maybe fix this later?
    """
    asynchronous interaction with the PasteBin API
    """
    def __init__(self, api_dev_key):
        self.api_dev_key = api_dev_key
    
    async def create_paste(
        self,
        api_paste_code:str,
        api_paste_private:int=0,
        api_paste_name:str=None,
        api_paste_expire_date:str=None,
        api_paste_format:str=None,
    ):
        """
        Create a new paste and if successful, return its url
        """
        data = {
            "api_dev_key": self.api_dev_key,
            "api_paste_code": api_paste_code,
            "api_paste_private": api_paste_private,
            "api_paste_name": api_paste_name,
            "api_paste_expire_date": api_paste_expire_date,
            "api_paste_format": api_paste_format,
            "api_option": "paste",
        }
        # Filter data and remove dictionary None keys.
        filtered_data = {k: v for k, v in data.items() if v is not None}

        async with aiohttp.ClientSession() as session:
            async with session.post("https://pastebin.com/api/api_post.php",data=filtered_data) as resp:
                return await resp.text()