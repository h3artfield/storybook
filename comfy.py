import websocket  # NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import uuid
import json
import urllib.request
import urllib.parse

server_address = "127.0.0.1:8188"
# client_id = str(uuid.uuid4())


class ComfyClient:
    def __init__(self, server_address, client_id=None, ws=None):
        self.server_address = server_address
        if client_id is None:
            client_id = str(uuid.uuid4())
        self.client_id = client_id
        if ws is None:
            ws = websocket.WebSocket()
            ws.timeout = 90
            ws.connect("ws://{}/ws?clientId={}".format(self.server_address, self.client_id))
        self.ws = ws

    def queue_prompt(self, prompt):
        p = {"prompt": prompt, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request("http://{}/prompt".format(self.server_address), data=data)
        return json.loads(urllib.request.urlopen(req).read())

    def get_image(self, filename, subfolder, folder_type):
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen("http://{}/view?{}".format(self.server_address, url_values)) as response:
            return response.read()

    def get_history(self, prompt_id):
        with urllib.request.urlopen("http://{}/history/{}".format(self.server_address, prompt_id)) as response:
            return json.loads(response.read())

    def get_images(self, prompt):
        prompt_id = self.queue_prompt(prompt)['prompt_id']
        output_images = {}
        while True:
            print('receiving...')
            out = self.ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['node'] is None and data['prompt_id'] == prompt_id:
                        break  # Execution is done
            else:
                print("shitting the bed")
                continue  # previews are binary data

        print('Get History')
        history = self.get_history(prompt_id)[prompt_id]
        for node_id in history['outputs']:
            node_output = history['outputs'][node_id]
            images_output = []
            if 'images' in node_output:
                for image in node_output['images']:
                    image_data = self.get_image(image['filename'], image['subfolder'], image['type'])
                    images_output.append(image_data)
            output_images[node_id] = images_output

        print('done')
        return output_images


if __name__ == '__main__':
    with open('clip_workflow_api.json', encoding='utf-8') as f:
        prompt = json.load(f)

    prompt["2"]["inputs"]["text"] = "gray cat, big eyes, big arms, short tail, stripes, tabby, excited"

    client = ComfyClient(server_address=server_address)
    images = client.get_images(prompt)

    for node_id in images:
        for image_data in images[node_id]:
            from PIL import Image
            import io

            image = Image.open(io.BytesIO(image_data))
            image.show()
