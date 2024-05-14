from datetime import datetime
import secrets
import string
import tensorflow as tf
from tensorflow.keras import backend
from tensorflow.keras.preprocessing import image
import base64
from io import BytesIO
import cv2
import numpy as np
from PIL import Image
from rembg import remove
import naite_db

# 현재 시간을 기준으로 고유한 파일 이름 생성
def generate_unique_filename():
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")
    random_string = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(8))  # 8자리 무작위 문자열 생성
    unique_filename = f"image_{timestamp}_{random_string}.jpg"
    return unique_filename

#모델 구조 가져오기
# 모델 망구성방식(토폴로지)에 대한 정보가 담긴 json 파일, 가중치를 저장하는 .h5 파일 

def recall_m(y_true, y_pred):
    true_positives = backend.sum(backend.round(backend.clip(y_true * y_pred, 0, 1)))
    possible_positives = backend.sum(backend.round(backend.clip(y_true, 0, 1)))
    recall = true_positives / (possible_positives + backend.epsilon())
    return recall

def precision_m(y_true, y_pred):
    true_positives = backend.sum(backend.round(backend.clip(y_true * y_pred, 0, 1)))
    predicted_positives = backend.sum(backend.round(backend.clip(y_pred, 0, 1)))
    precision = true_positives / (predicted_positives + backend.epsilon())
    return precision

def f1_m(y_true, y_pred):
    precision = precision_m(y_true, y_pred)
    recall = recall_m(y_true, y_pred)
    return 2*((precision*recall)/(precision+recall+backend.epsilon()))



def process_and_save_image(file, bucket, model, product_id:int):
    db_class = naite_db.Database()
    # base64 이미지 데이터를 디코딩하여 이미지로 변환
    image_data = base64.b64decode(file)
    img = Image.open(BytesIO(image_data))

    # 이미지 처리
    out = remove(img)
    white_bg = Image.new("RGBA", img.size, "WHITE")
    white_bg.paste(img, (0, 0), out)
    white_bg = white_bg.convert("RGB")
    open_cv_image = np.array(white_bg)
    open_cv_image = open_cv_image[:, :, ::-1]  # Convert RGB to BGR

    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        c = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(c)
        crop_img = open_cv_image[y:y+h, x:x+w]

    crop_img_pil = Image.fromarray(crop_img[:, :, ::-1])  # BGR to RGB

    # 이미지 크기 조정
    target_size = (299, 299)
    resized_image = crop_img_pil.resize(target_size)

    # 업로드할 파일을 GCP에 저장할 때의 이름 생성
    destination_blob_name = generate_unique_filename()

    # 이미지를 Google Cloud Storage에 업로드
    blob = bucket.blob(destination_blob_name)
    with BytesIO() as output:
        resized_image.save(output, format='JPEG')
        output.seek(0)
        blob.upload_from_file(output, content_type='image/jpeg')

    sql = "INSERT INTO Photos(user_email, product_id, image_path) VALUES (%s, %s, %s)"
    values = ('jjjk0605@naver.com',product_id,'https://storage.googleapis.com/exaple_naite/'+destination_blob_name)
    db_class.execute(sql, values)
    db_class.commit()
    db_class.close()

    x = image.img_to_array(resized_image)
    x = np.expand_dims(x, axis=0)
    x /= 255.

    output = model.predict(x)
    class_probabilities = tf.nn.softmax(output[0]).numpy().tolist()
    print(class_probabilities)

    max_value = max(class_probabilities)
    max_index = class_probabilities.index(max_value)

    return {"predicted_percent": class_probabilities, "predicted_class": max_index, "url": 'https://storage.googleapis.com/exaple_naite/'+destination_blob_name}


def getInfo(product_id):
    db_class = naite_db.Database()
    sql = "SELECT select_tip, efficacy, standard FROM Information JOIN Products ON Information.product_id=Products.product_id WHERE Products.product_name=%s;"
    info = db_class.executeOne(sql, (product_id))
    db_class.close()
    return info
