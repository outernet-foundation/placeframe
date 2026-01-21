#include <DotNet/UnityEngine/SceneManagement/Scene.h>
#include <DotNet/UnityEngine/GameObject.h>
#include <DotNet/System/Array1.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>



namespace DotNet::UnityEngine::SceneManagement {

void* (*DotNet::UnityEngine::SceneManagement::Scene::CallGetRootGameObjects_1B2M2Y8AsgTpgAmY7PhCfg)(const ::DotNet::UnityEngine::SceneManagement::Scene* thiz, void** reinteropException) = nullptr;


::DotNet::System::Array1<::DotNet::UnityEngine::GameObject> Scene::GetRootGameObjects() const {
    void* reinteropException = nullptr;
    auto result = CallGetRootGameObjects_1B2M2Y8AsgTpgAmY7PhCfg(&(*this), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Array1<::DotNet::UnityEngine::GameObject>(::DotNet::Reinterop::ObjectHandle(result));
}


} // namespace DotNet::UnityEngine::SceneManagement


