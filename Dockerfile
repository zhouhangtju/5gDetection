FROM python:3.7.17
WORKDIR /home/
ADD ./ ./code-dev
RUN pip install --no-cache -r code-dev/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
CMD ["python","/home/code-dev/run.py"]