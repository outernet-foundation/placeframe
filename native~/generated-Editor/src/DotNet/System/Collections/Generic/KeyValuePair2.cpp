#include <DotNet/System/String.h>
#include <DotNet/System/Collections/Generic/KeyValuePair2.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>



namespace DotNet::System::Collections::Generic {

KeyValuePair2<::DotNet::System::String, ::DotNet::System::String>::KeyValuePair2(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


KeyValuePair2<::DotNet::System::String, ::DotNet::System::String>::KeyValuePair2(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool KeyValuePair2<::DotNet::System::String, ::DotNet::System::String>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool KeyValuePair2<::DotNet::System::String, ::DotNet::System::String>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& KeyValuePair2<::DotNet::System::String, ::DotNet::System::String>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& KeyValuePair2<::DotNet::System::String, ::DotNet::System::String>::GetHandle() {
    return this->_handle;
}


void* (*DotNet::System::Collections::Generic::KeyValuePair2<::DotNet::System::String, ::DotNet::System::String>::Property_get_Key)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String KeyValuePair2<::DotNet::System::String, ::DotNet::System::String>::Key() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Key((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::System::Collections::Generic::KeyValuePair2<::DotNet::System::String, ::DotNet::System::String>::Property_get_Value)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String KeyValuePair2<::DotNet::System::String, ::DotNet::System::String>::Value() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Value((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


} // namespace DotNet::System::Collections::Generic


