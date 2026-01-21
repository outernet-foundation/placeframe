#include <DotNet/CesiumForUnity/CesiumSampleHeightResult.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/Object.h>
#include <DotNet/Unity/Mathematics/double3.h>
#include <DotNet/System/Array1.h>
#include <DotNet/System/String.h>



namespace DotNet::CesiumForUnity {

CesiumSampleHeightResult::CesiumSampleHeightResult(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumSampleHeightResult::CesiumSampleHeightResult(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool CesiumSampleHeightResult::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool CesiumSampleHeightResult::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& CesiumSampleHeightResult::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumSampleHeightResult::GetHandle() {
    return this->_handle;
}


void* (*CesiumSampleHeightResult::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


CesiumSampleHeightResult::CesiumSampleHeightResult()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


CesiumSampleHeightResult::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::CesiumSampleHeightResult::Property_get_longitudeLatitudeHeightPositions)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Array1<::DotNet::Unity::Mathematics::double3> CesiumSampleHeightResult::longitudeLatitudeHeightPositions() const {
    void* reinteropException = nullptr;
    auto result = Property_get_longitudeLatitudeHeightPositions((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Array1<::DotNet::Unity::Mathematics::double3>(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumSampleHeightResult::Property_set_longitudeLatitudeHeightPositions)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumSampleHeightResult::longitudeLatitudeHeightPositions(const ::DotNet::System::Array1<::DotNet::Unity::Mathematics::double3>& value) const {
    void* reinteropException = nullptr;
    Property_set_longitudeLatitudeHeightPositions((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumSampleHeightResult::Property_get_sampleSuccess)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Array1<bool> CesiumSampleHeightResult::sampleSuccess() const {
    void* reinteropException = nullptr;
    auto result = Property_get_sampleSuccess((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Array1<bool>(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumSampleHeightResult::Property_set_sampleSuccess)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumSampleHeightResult::sampleSuccess(const ::DotNet::System::Array1<bool>& value) const {
    void* reinteropException = nullptr;
    Property_set_sampleSuccess((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumSampleHeightResult::Property_get_warnings)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Array1<::DotNet::System::String> CesiumSampleHeightResult::warnings() const {
    void* reinteropException = nullptr;
    auto result = Property_get_warnings((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Array1<::DotNet::System::String>(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumSampleHeightResult::Property_set_warnings)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumSampleHeightResult::warnings(const ::DotNet::System::Array1<::DotNet::System::String>& value) const {
    void* reinteropException = nullptr;
    Property_set_warnings((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::CesiumForUnity


