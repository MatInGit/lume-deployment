# docker login harbor.stfc.ac.uk
docker build --pull --rm -f "Dockerfile" -t harbor.stfc.ac.uk/isis-accelerator-controls/lume-deploy:interactive "." &&
docker push harbor.stfc.ac.uk/isis-accelerator-controls/lume-deploy:interactive