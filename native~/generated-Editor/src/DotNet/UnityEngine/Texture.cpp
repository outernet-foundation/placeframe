#include <DotNet/UnityEngine/Texture.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/Object.h>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/UnityEngine/TextureWrapMode.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/FilterMode.h>
#include <DotNet/System/String.h>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>



namespace DotNet::UnityEngine {

Texture::Texture(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Texture::Texture(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& Texture::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Texture::GetHandle() {
    return this->_handle;
}


Texture::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Texture::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::uint32_t (*DotNet::UnityEngine::Texture::Property_get_wrapMode)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::TextureWrapMode Texture::wrapMode() const {
    void* reinteropException = nullptr;
    auto result = Property_get_wrapMode((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::TextureWrapMode(result);
}


void (*DotNet::UnityEngine::Texture::Property_set_wrapMode)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void Texture::wrapMode(::DotNet::UnityEngine::TextureWrapMode value) const {
    void* reinteropException = nullptr;
    Property_set_wrapMode((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::UnityEngine::Texture::Property_get_anisoLevel)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Texture::anisoLevel() const {
    void* reinteropException = nullptr;
    auto result = Property_get_anisoLevel((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::Texture::Property_set_anisoLevel)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void Texture::anisoLevel(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_anisoLevel((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::UnityEngine::Texture::Property_get_filterMode)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::FilterMode Texture::filterMode() const {
    void* reinteropException = nullptr;
    auto result = Property_get_filterMode((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::FilterMode(result);
}


void (*DotNet::UnityEngine::Texture::Property_set_filterMode)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void Texture::filterMode(::DotNet::UnityEngine::FilterMode value) const {
    void* reinteropException = nullptr;
    Property_set_filterMode((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::UnityEngine::Texture::Property_get_wrapModeU)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::TextureWrapMode Texture::wrapModeU() const {
    void* reinteropException = nullptr;
    auto result = Property_get_wrapModeU((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::TextureWrapMode(result);
}


void (*DotNet::UnityEngine::Texture::Property_set_wrapModeU)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void Texture::wrapModeU(::DotNet::UnityEngine::TextureWrapMode value) const {
    void* reinteropException = nullptr;
    Property_set_wrapModeU((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::UnityEngine::Texture::Property_get_wrapModeV)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::TextureWrapMode Texture::wrapModeV() const {
    void* reinteropException = nullptr;
    auto result = Property_get_wrapModeV((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::TextureWrapMode(result);
}


void (*DotNet::UnityEngine::Texture::Property_set_wrapModeV)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void Texture::wrapModeV(::DotNet::UnityEngine::TextureWrapMode value) const {
    void* reinteropException = nullptr;
    Property_set_wrapModeV((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::UnityEngine::Texture::Property_get_wrapModeW)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::TextureWrapMode Texture::wrapModeW() const {
    void* reinteropException = nullptr;
    auto result = Property_get_wrapModeW((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::TextureWrapMode(result);
}


void (*DotNet::UnityEngine::Texture::Property_set_wrapModeW)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void Texture::wrapModeW(::DotNet::UnityEngine::TextureWrapMode value) const {
    void* reinteropException = nullptr;
    Property_set_wrapModeW((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::UnityEngine::Texture::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String Texture::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Texture::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void Texture::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::UnityEngine::Texture::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> Texture::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::UnityEngine::Texture::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void Texture::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::UnityEngine::Texture::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool Texture::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool Texture::operator==(const Texture& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool Texture::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool Texture::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::UnityEngine::Texture::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool Texture::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool Texture::operator!=(const Texture& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool Texture::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool Texture::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::UnityEngine::Texture::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Texture::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::UnityEngine


