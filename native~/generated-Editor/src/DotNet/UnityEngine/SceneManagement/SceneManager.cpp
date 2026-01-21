#include <DotNet/UnityEngine/SceneManagement/SceneManager.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/SceneManagement/Scene.h>



namespace DotNet::UnityEngine::SceneManagement {

SceneManager::SceneManager(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


SceneManager::SceneManager(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool SceneManager::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool SceneManager::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& SceneManager::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& SceneManager::GetHandle() {
    return this->_handle;
}


SceneManager::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::int32_t (*DotNet::UnityEngine::SceneManagement::SceneManager::Property_get_sceneCount)(void** reinteropException) = nullptr;


::std::int32_t SceneManager::sceneCount() {
    void* reinteropException = nullptr;
    auto result = Property_get_sceneCount(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::SceneManagement::SceneManager::CallGetSceneAt_7IHapUgMd7RT8__gH__cKUrw)(::std::int32_t index, ::DotNet::UnityEngine::SceneManagement::Scene* pReturnValue, void** reinteropException) = nullptr;


::DotNet::UnityEngine::SceneManagement::Scene SceneManager::GetSceneAt(::std::int32_t index) {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::SceneManagement::Scene result;
    CallGetSceneAt_7IHapUgMd7RT8__gH__cKUrw(index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::UnityEngine::SceneManagement


