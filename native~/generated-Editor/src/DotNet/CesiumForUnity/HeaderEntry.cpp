#include <DotNet/CesiumForUnity/HeaderEntry.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/System/String.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>



namespace DotNet::CesiumForUnity {

HeaderEntry::HeaderEntry(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


HeaderEntry::HeaderEntry(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool HeaderEntry::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool HeaderEntry::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& HeaderEntry::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& HeaderEntry::GetHandle() {
    return this->_handle;
}


HeaderEntry::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::HeaderEntry::Field_get_Name)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::HeaderEntry::Field_set_Name)(void* thiz, void* value, void** reinteropException) = nullptr;


::DotNet::System::String HeaderEntry::Name() const {
    void* reinteropException = nullptr;
    auto result = Field_get_Name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void HeaderEntry::Name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Field_set_Name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


void* (*DotNet::CesiumForUnity::HeaderEntry::Field_get_Value)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::HeaderEntry::Field_set_Value)(void* thiz, void* value, void** reinteropException) = nullptr;


::DotNet::System::String HeaderEntry::Value() const {
    void* reinteropException = nullptr;
    auto result = Field_get_Value((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void HeaderEntry::Value(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Field_set_Value((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


} // namespace DotNet::CesiumForUnity


