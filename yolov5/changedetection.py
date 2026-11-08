import os
import base64
import cv2
import pathlib
import requests
from datetime import datetime


class ChangeDetection:
    result_prev = []
    HOST = os.getenv('AUTH_SERVER_URL', 'https://mwp2.drafts.md')
    username = os.getenv('AUTH_SERVER_USERNAME', 'klee')
    password = os.environ['AUTH_SERVER_PASSWORD']
    title = ''
    text = ''
    objects = []

    def __init__(self, names):
        self.result_prev = [0 for i in range(len(names))]

    def add(self, names, detected_current, save_dir, image):
        self.title = ''
        self.text = ''
        change_flag = 0
        i = 0
        while i < len(self.result_prev):
            if self.result_prev[i] == 0 and detected_current[i] == 1:
                change_flag = 1
                self.title = names[i]
                self.text += names[i] + ", "
            i += 1

        self.result_prev = detected_current[:]
        self.objects = [names[i] for i in range(len(detected_current)) if detected_current[i] == 1]

        if change_flag == 1:
            self.send(save_dir, image)

    def send(self, save_dir, image):
        now = datetime.now()
        now.isoformat()

        today = datetime.now()
        save_path = os.getcwd() / save_dir / 'detected' / str(today.year) / str(today.month) / str(today.day)
        pathlib.Path(save_path).mkdir(parents=True, exist_ok=True)

        full_path = save_path / '{0}-{1}-{2}-{3}.jpg'.format(today.hour, today.minute, today.second, today.microsecond)

        cv2.imwrite(full_path, image)
        with open(full_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode()

        data = {
            'title': self.title,
            'text': self.text,
            'created_date': now.isoformat(),
            'published_date': now.isoformat(),
            'image': encoded,
            'objects': self.objects,
        }
        res = requests.post(self.HOST + '/ingest', json=data, auth=(self.username, self.password), timeout=120)
        print(res, res.text)
