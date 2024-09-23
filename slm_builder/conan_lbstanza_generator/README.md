# Creating and Uploading new version of lbstanzagenerator_pyreq
```
cd slm_builder/conan_lbstanza_generator
conan create .
export CONAN_USER_LOGIN_ARTIFACTORY=jitx
export CONAN_PASSWORD_ARTIFACTORY=...
conan upload -r artifactory lbstanzagenerator_pyreq
```

