#include <DotNet/CesiumForUnity/CesiumSampleHeightResult.h>
#include <DotNet/System/Threading/Tasks/Task1.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Threading/Tasks/Task.h>
#include <DotNet/System/Object.h>



namespace DotNet::System::Threading::Tasks {

Task1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::Task1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Task1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::Task1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Task1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Task1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Task1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Task1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::GetHandle() {
    return this->_handle;
}


Task1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::operator ::DotNet::System::Threading::Tasks::Task() const {
    return ::DotNet::System::Threading::Tasks::Task(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Task1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


} // namespace DotNet::System::Threading::Tasks


