# docker login harbor.stfc.ac.uk
# set build time variables
export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
export VCS_REF=$(git rev-parse --short HEAD)

# if build-info file exists, remove it
if [ -f build-info ]; then
    rm build-info.json
fi

# create build-info file
touch build-info.json
echo "{" >> build-info.json
echo "  \"build-date\": \"$BUILD_DATE\"," >> build-info.json
echo "  \"vcs-ref\": \"$VCS_REF\"" >> build-info.json
echo "}" >> build-info.json

docker build --pull --rm -f "Dockerfile" -t harbor.stfc.ac.uk/isis-accelerator-controls/lume-deploy:dev "." &&
docker push harbor.stfc.ac.uk/isis-accelerator-controls/lume-deploy:dev

docker build --pull --rm -f "Dockerfile.interactive" -t harbor.stfc.ac.uk/isis-accelerator-controls/lume-deploy:interactive "." &&
docker push harbor.stfc.ac.uk/isis-accelerator-controls/lume-deploy:interactive
