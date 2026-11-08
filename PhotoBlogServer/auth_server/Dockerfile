# Alpine's py3-opencv pulls in Qt, GTK, LLVM and FFmpeg (about 600 MB), so build
# only the modules the face pipeline needs, statically linked into one extension.
FROM alpine:3.22 AS opencv
ARG OPENCV_VERSION=4.11.0
RUN apk add --no-cache build-base cmake ninja linux-headers python3-dev py3-numpy-dev \
    && wget -qO- https://github.com/opencv/opencv/archive/refs/tags/${OPENCV_VERSION}.tar.gz | tar xz -C /tmp \
    && cmake -S /tmp/opencv-${OPENCV_VERSION} -B /tmp/build -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/opt/opencv \
        -DBUILD_LIST=core,imgproc,imgcodecs,dnn,objdetect,python3 \
        -DBUILD_SHARED_LIBS=OFF \
        -DBUILD_JPEG=ON -DBUILD_PROTOBUF=ON -DPROTOBUF_UPDATE_FILES=OFF \
        -DBUILD_TESTS=OFF -DBUILD_PERF_TESTS=OFF -DBUILD_EXAMPLES=OFF -DBUILD_DOCS=OFF \
        -DBUILD_opencv_apps=OFF -DBUILD_JAVA=OFF -DBUILD_opencv_python2=OFF \
        -DWITH_PNG=OFF -DWITH_TIFF=OFF -DWITH_WEBP=OFF -DWITH_OPENJPEG=OFF -DWITH_JASPER=OFF \
        -DWITH_OPENEXR=OFF -DWITH_IMGCODEC_HDR=OFF -DWITH_IMGCODEC_SUNRASTER=OFF \
        -DWITH_IMGCODEC_PXM=OFF -DWITH_IMGCODEC_PFM=OFF \
        -DWITH_FFMPEG=OFF -DWITH_GSTREAMER=OFF -DWITH_V4L=OFF -DWITH_GTK=OFF -DWITH_QT=OFF \
        -DWITH_OPENCL=OFF -DWITH_IPP=OFF -DWITH_ITT=OFF -DWITH_ADE=OFF -DWITH_EIGEN=OFF \
        -DWITH_LAPACK=OFF -DWITH_CAROTENE=ON \
        -DOPENCV_GENERATE_PKGCONFIG=OFF -DOPENCV_SKIP_PYTHON_LOADER=ON \
        -DOPENCV_PYTHON3_INSTALL_PATH=/opt/python \
    && cmake --build /tmp/build --target install \
    && strip --strip-unneeded /opt/python/*.so

FROM alpine:3.22
RUN apk add --no-cache python3 py3-numpy libstdc++ \
    && adduser -D -H -u 10001 app \
    && mkdir -p /data /models \
    && chown app:app /data

COPY --from=opencv /opt/python/ /usr/lib/python3.12/site-packages/
ADD --chmod=444 https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx /models/
ADD --chmod=444 https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx /models/
WORKDIR /srv
COPY app/ /srv/app/

USER app
VOLUME /data
EXPOSE 9000
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1:9000/health || exit 1

CMD ["python3", "-m", "app"]
