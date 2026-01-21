#include <DotNet/CesiumForUnity/CesiumPropertyArray.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/Object.h>
#include <DotNet/CesiumForUnity/CesiumMetadataValueType.h>
#include <DotNet/CesiumForUnity/CesiumMetadataValue.h>
#include <DotNet/System/Array1.h>

namespace DotNet::CesiumForUnity {
struct CesiumMetadataValueType;
}

namespace DotNet::CesiumForUnity {

CesiumPropertyArray::CesiumPropertyArray(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumPropertyArray::CesiumPropertyArray(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool CesiumPropertyArray::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool CesiumPropertyArray::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& CesiumPropertyArray::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumPropertyArray::GetHandle() {
    return this->_handle;
}


void* (*CesiumPropertyArray::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


CesiumPropertyArray::CesiumPropertyArray()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


CesiumPropertyArray::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::CesiumForUnity::CesiumPropertyArray::Property_get_elementValueType)(void* thiz, ::DotNet::CesiumForUnity::CesiumMetadataValueType* pReturnValue, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumMetadataValueType CesiumPropertyArray::elementValueType() const {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumMetadataValueType result;
    Property_get_elementValueType((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumPropertyArray::Property_set_elementValueType)(void* thiz, const ::DotNet::CesiumForUnity::CesiumMetadataValueType* value, void** reinteropException) = nullptr;


void CesiumPropertyArray::elementValueType(const ::DotNet::CesiumForUnity::CesiumMetadataValueType& value) const {
    void* reinteropException = nullptr;
    Property_set_elementValueType((*this).GetHandle().GetRaw(), &value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumPropertyArray::Property_get_values)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumMetadataValue> CesiumPropertyArray::values() const {
    void* reinteropException = nullptr;
    auto result = Property_get_values((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumPropertyArray::Property_set_values)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumPropertyArray::values(const ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>& value) const {
    void* reinteropException = nullptr;
    Property_set_values((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::CesiumForUnity


