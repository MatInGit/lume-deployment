# set build time variables
export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
export VCS_REF=$(git rev-parse --short HEAD)
export VERSION=0.1.6.dev6 #   $(hatch version)

# # if build-info file exists, remove it
# if [ -f build-info ]; then
#     rm build-info.json

# # # create build-info file
# touch build-info.json
# echo "{" >> build-info.json
# echo "  \"build-date\": \"$BUILD_DATE\"," >> build-info.json
# echo "  \"vcs-ref\": \"$VCS_REF\"" >> build-info.json
# echo "}" >> build-info.json

docker build --pull --rm --target vanilla -f "Dockerfile" -t harbor.stfc.ac.uk/isis-accelerator-controls/poly-lithic:base-$VERSION "."
docker build --pull --rm --target torch -f "Dockerfile" -t harbor.stfc.ac.uk/isis-accelerator-controls/poly-lithic:torch-$VERSION "."
docker build --pull --rm --target tensorflow -f "Dockerfile" -t harbor.stfc.ac.uk/isis-accelerator-controls/poly-lithic:tensorflow-$VERSION "."

# docker push harbor.stfc.ac.uk/isis-accelerator-controls/lume-deploy:dev13

# docker build --pull --rm -f "Dockerfile.interactive" -t harbor.stfc.ac.uk/isis-accelerator-controls/lume-deploy:interactive13 "." &&
# docker push harbor.stfc.ac.uk/isis-accelerator-controls/lume-deploy:interactive13

docker push harbor.stfc.ac.uk/isis-accelerator-controls/poly-lithic:base-$VERSION
docker push harbor.stfc.ac.uk/isis-accelerator-controls/poly-lithic:torch-$VERSION
docker push harbor.stfc.ac.uk/isis-accelerator-controls/poly-lithic:tensorflow-$VERSION

# docker hub retag and push matindocker/poly-lithic
docker tag harbor.stfc.ac.uk/isis-accelerator-controls/poly-lithic:base-$VERSION matindocker/poly-lithic:base-$VERSION
docker tag harbor.stfc.ac.uk/isis-accelerator-controls/poly-lithic:torch-$VERSION matindocker/poly-lithic:torch-$VERSION
docker tag harbor.stfc.ac.uk/isis-accelerator-controls/poly-lithic:tensorflow-$VERSION matindocker/poly-lithic:tensorflow-$VERSION

docker push matindocker/poly-lithic:base-$VERSION
docker push matindocker/poly-lithic:torch-$VERSION
docker push matindocker/poly-lithic:tensorflow-$VERSION
