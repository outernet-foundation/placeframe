#include <DotNet/UnityEngine/Time.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropNativeException.h>



namespace DotNet::UnityEngine {

Time::Time(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Time::Time(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Time::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Time::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Time::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Time::GetHandle() {
    return this->_handle;
}


Time::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::int32_t (*DotNet::UnityEngine::Time::Property_get_frameCount)(void** reinteropException) = nullptr;


::std::int32_t Time::frameCount() {
    void* reinteropException = nullptr;
    auto result = Property_get_frameCount(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


float (*DotNet::UnityEngine::Time::Property_get_deltaTime)(void** reinteropException) = nullptr;


float Time::deltaTime() {
    void* reinteropException = nullptr;
    auto result = Property_get_deltaTime(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::UnityEngine


