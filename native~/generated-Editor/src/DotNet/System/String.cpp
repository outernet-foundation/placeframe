#include <DotNet/System/String.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/StringComparison.h>
#include <DotNet/System/Array1.h>
#include <DotNet/System/Text/Encoding.h>
#include <DotNet/System/Runtime/InteropServices/Marshal.h>



namespace DotNet::System {

String::String(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


String::String(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& String::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& String::GetHandle() {
    return this->_handle;
}


String::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::int32_t (*DotNet::System::String::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t String::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::uint8_t (*DotNet::System::String::Callop_Equality_46DLRq__QwpwCx8Uf20Cl7A)(void* a, void* b, void** reinteropException) = nullptr;


bool String::operator==(const ::DotNet::System::String& rhs) const {
  return op_Equality(*this, rhs);
}


bool String::op_Equality(const ::DotNet::System::String& a, const ::DotNet::System::String& b) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_46DLRq__QwpwCx8Uf20Cl7A(a.GetHandle().GetRaw(), b.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::System::String::Callop_Inequality_46DLRq__QwpwCx8Uf20Cl7A)(void* a, void* b, void** reinteropException) = nullptr;


bool String::operator!=(const ::DotNet::System::String& rhs) const {
  return op_Inequality(*this, rhs);
}


bool String::op_Inequality(const ::DotNet::System::String& a, const ::DotNet::System::String& b) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_46DLRq__QwpwCx8Uf20Cl7A(a.GetHandle().GetRaw(), b.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::System::String::CallContains_GImL1A5rlEQAx14EidO2oA)(void* thiz, void* value, ::std::uint32_t comparisonType, void** reinteropException) = nullptr;


bool String::Contains(const ::DotNet::System::String& value, ::DotNet::System::StringComparison comparisonType) const {
    void* reinteropException = nullptr;
    auto result = CallContains_GImL1A5rlEQAx14EidO2oA((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), ::std::uint32_t(comparisonType), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::System::String::CallEquals_46DLRq__QwpwCx8Uf20Cl7A)(void* a, void* b, void** reinteropException) = nullptr;


bool String::Equals(const ::DotNet::System::String& a, const ::DotNet::System::String& b) {
    void* reinteropException = nullptr;
    auto result = CallEquals_46DLRq__QwpwCx8Uf20Cl7A(a.GetHandle().GetRaw(), b.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::System::String::CallIsNullOrEmpty_ZOWEGUlscki07yVzH4i4ww)(void* value, void** reinteropException) = nullptr;


bool String::IsNullOrEmpty(const ::DotNet::System::String& value) {
    void* reinteropException = nullptr;
    auto result = CallIsNullOrEmpty_ZOWEGUlscki07yVzH4i4ww(value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void* (*DotNet::System::String::CallConcat_yq7nlytzIFp8a79slfH_mw)(void* arg0, void* arg1, void** reinteropException) = nullptr;


::DotNet::System::String String::Concat(const ::DotNet::System::Object& arg0, const ::DotNet::System::Object& arg1) {
    void* reinteropException = nullptr;
    auto result = CallConcat_yq7nlytzIFp8a79slfH_mw(arg0.GetHandle().GetRaw(), arg1.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::System::String::CallConcat_OM9SoWVFMTHXvbepMyUchw)(void* str0, void* str1, void** reinteropException) = nullptr;


::DotNet::System::String String::Concat(const ::DotNet::System::String& str0, const ::DotNet::System::String& str1) {
    void* reinteropException = nullptr;
    auto result = CallConcat_OM9SoWVFMTHXvbepMyUchw(str0.GetHandle().GetRaw(), str1.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::System::String::CallJoin_ZMypEy2QfaUCbJCXuGMgzg)(void* separator, void* value, void** reinteropException) = nullptr;


::DotNet::System::String String::Join(const ::DotNet::System::String& separator, const ::DotNet::System::Array1<::DotNet::System::String>& value) {
    void* reinteropException = nullptr;
    auto result = CallJoin_ZMypEy2QfaUCbJCXuGMgzg(separator.GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


::std::uint8_t (*DotNet::System::String::CallIsNullOrWhiteSpace_ZOWEGUlscki07yVzH4i4ww)(void* value, void** reinteropException) = nullptr;


bool String::IsNullOrWhiteSpace(const ::DotNet::System::String& value) {
    void* reinteropException = nullptr;
    auto result = CallIsNullOrWhiteSpace_ZOWEGUlscki07yVzH4i4ww(value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


String::String(const ::std::string& s) : _handle() {
  String result = ::DotNet::System::Text::Encoding::UTF8().GetString(
    const_cast<std::uint8_t*>(reinterpret_cast<const std::uint8_t*>(s.data())),
    std::int32_t(s.size()));
  this->_handle = std::move(result._handle);
}


std::string String::ToStlString() const {
  if (*this == nullptr)
    return std::string();

  void* p = ::DotNet::System::Runtime::InteropServices::Marshal::StringToCoTaskMemUTF8(*this);
  try {
    std::string result = static_cast<char*>(p);
    ::DotNet::System::Runtime::InteropServices::Marshal::FreeCoTaskMem(p);
    return result;
  } catch (...) {
    ::DotNet::System::Runtime::InteropServices::Marshal::FreeCoTaskMem(p);
    throw;
  }
}


} // namespace DotNet::System


