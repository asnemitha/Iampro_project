import requests, json

payload = {
    "prompt": "Format the following two papers using your required citation format exactly. Paper 1: 'Deep Residual Learning for Image Recognition' by Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun. Venue: '2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR)'. Year: 2016. DOI: 10.1109/CVPR.2016.90. Paper 2: 'You Only Look Once: Unified, Real-Time Object Detection' by Joseph Redmon, Santosh Divvala, Ross Girshick, Ali Farhadi. Venue: '2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR)'. Year: 2016. DOI: 10.1109/CVPR.2016.91"
}

r = requests.post("http://127.0.0.1:8000/analyze", json=payload)
print(json.dumps(r.json(), indent=2))
