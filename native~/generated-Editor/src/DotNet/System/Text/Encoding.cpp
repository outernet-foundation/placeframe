#include <DotNet/System/Text/Encoding.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>
#include <DotNet/System/String.h>



namespace DotNet::System::Text {

Encoding::Encoding(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Encoding::Encoding(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Encoding::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Encoding::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Encoding::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Encoding::GetHandle() {
    return this->_handle;
}


Encoding::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::System::Text::Encoding::Property_get_UTF8)(void** reinteropException) = nullptr;


::DotNet::System::Text::Encoding Encoding::UTF8() {
    void* reinteropException = nullptr;
    auto result = Property_get_UTF8(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Text::Encoding(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::System::Text::Encoding::CallGetString_J_gIxYGOW0ecDuybXJZsCw)(void* thiz, ::std::uint8_t* bytes, ::std::int32_t byteCount, void** reinteropException) = nullptr;


::DotNet::System::String Encoding::GetString(::std::uint8_t* bytes, ::std::int32_t byteCount) const {
    void* reinteropException = nullptr;
    auto result = CallGetString_J_gIxYGOW0ecDuybXJZsCw((*this).GetHandle().GetRaw(), bytes, byteCount, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


} // namespace DotNet::System::Text


