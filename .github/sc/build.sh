#!/usr/bin/env bash
set -euo pipefail

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REG="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
IMG_TAG="${GITHUB_SHA::7}"
IMG_NAME="${ECR_REG}/${ECR_REPO}"

echo "Building ${IMG_NAME}:${IMG_TAG}"
docker build --tag "${IMG_NAME}:${IMG_TAG}" .
docker tag "${IMG_NAME}:${IMG_TAG}" "${IMG_NAME}:latest"

aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${ECR_REG}"

docker push "${IMG_NAME}:${IMG_TAG}"
docker push "${IMG_NAME}:latest"

{
  echo "ecr_registry=${ECR_REG}"
  echo "ecr_image=${IMG_NAME}"
  echo "image_tag=${IMG_TAG}"
} >> "${GITHUB_OUTPUT}"