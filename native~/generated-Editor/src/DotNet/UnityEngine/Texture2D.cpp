#include <DotNet/UnityEngine/Texture2D.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/TextureFormat.h>
#include <DotNet/UnityEngine/Texture.h>
#include <DotNet/UnityEngine/Object.h>
#include <DotNet/System/Object.h>
#include <DotNet/Unity/Collections/NativeArray1.h>
#include <DotNet/UnityEngine/TextureWrapMode.h>
#include <DotNet/UnityEngine/FilterMode.h>
#include <DotNet/System/String.h>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>



namespace DotNet::UnityEngine {

Texture2D::Texture2D(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Texture2D::Texture2D(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& Texture2D::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Texture2D::GetHandle() {
    return this->_handle;
}


void* (*Texture2D::Construct_7_RAqfRCmreonOQ53TO4Og)(::std::int32_t width, ::std::int32_t height, ::std::uint32_t textureFormat, ::std::uint8_t mipChain, ::std::uint8_t linear, void** reinteropException) = nullptr;


Texture2D::Texture2D(::std::int32_t width, ::std::int32_t height, ::DotNet::UnityEngine::TextureFormat textureFormat, bool mipChain, bool linear)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_7_RAqfRCmreonOQ53TO4Og(width, height, ::std::uint32_t(textureFormat), mipChain ? 1 : 0, linear ? 1 : 0, &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


void* (*Texture2D::Construct_IFL2bOqlLrYHuwg5z0d8Cg)(::std::int32_t width, ::std::int32_t height, ::std::uint32_t textureFormat, ::std::int32_t mipCount, ::std::uint8_t linear, void** reinteropException) = nullptr;


Texture2D::Texture2D(::std::int32_t width, ::std::int32_t height, ::DotNet::UnityEngine::TextureFormat textureFormat, ::std::int32_t mipCount, bool linear)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_IFL2bOqlLrYHuwg5z0d8Cg(width, height, ::std::uint32_t(textureFormat), mipCount, linear ? 1 : 0, &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


Texture2D::operator ::DotNet::UnityEngine::Texture() const {
    return ::DotNet::UnityEngine::Texture(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Texture2D::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Texture2D::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::UnityEngine::Texture2D::CallLoadRawTextureData_C8JeOQhDs2O3mbZ4aC21YA)(void* thiz, void* data, ::std::int32_t size, void** reinteropException) = nullptr;


void Texture2D::LoadRawTextureData(void* data, ::std::int32_t size) const {
    void* reinteropException = nullptr;
    CallLoadRawTextureData_C8JeOQhDs2O3mbZ4aC21YA((*this).GetHandle().GetRaw(), data, size, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::UnityEngine::Texture2D::CallGetRawTextureData_z79ECk55IqLfMIqXBYg_8w)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t> Texture2D::GetRawTextureData<::std::uint8_t>() const {
    void* reinteropException = nullptr;
    auto result = CallGetRawTextureData_z79ECk55IqLfMIqXBYg_8w((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Texture2D::CallApply_FZiaA8ur57jmvHTqox9Bng)(void* thiz, ::std::uint8_t updateMipmaps, ::std::uint8_t makeNoLongerReadable, void** reinteropException) = nullptr;


void Texture2D::Apply(bool updateMipmaps, bool makeNoLongerReadable) const {
    void* reinteropException = nullptr;
    CallApply_FZiaA8ur57jmvHTqox9Bng((*this).GetHandle().GetRaw(), updateMipmaps ? 1 : 0, makeNoLongerReadable ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::UnityEngine::Texture2D::Property_get_wrapMode)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::TextureWrapMode Texture2D::wrapMode() const {
    void* reinteropException = nullptr;
    auto result = Property_get_wrapMode((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::TextureWrapMode(result);
}


void (*DotNet::UnityEngine::Texture2D::Property_set_wrapMode)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void Texture2D::wrapMode(::DotNet::UnityEngine::TextureWrapMode value) const {
    void* reinteropException = nullptr;
    Property_set_wrapMode((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::UnityEngine::Texture2D::Property_get_anisoLevel)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Texture2D::anisoLevel() const {
    void* reinteropException = nullptr;
    auto result = Property_get_anisoLevel((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::Texture2D::Property_set_anisoLevel)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void Texture2D::anisoLevel(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_anisoLevel((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::UnityEngine::Texture2D::Property_get_filterMode)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::FilterMode Texture2D::filterMode() const {
    void* reinteropException = nullptr;
    auto result = Property_get_filterMode((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::FilterMode(result);
}


void (*DotNet::UnityEngine::Texture2D::Property_set_filterMode)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void Texture2D::filterMode(::DotNet::UnityEngine::FilterMode value) const {
    void* reinteropException = nullptr;
    Property_set_filterMode((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::UnityEngine::Texture2D::Property_get_wrapModeU)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::TextureWrapMode Texture2D::wrapModeU() const {
    void* reinteropException = nullptr;
    auto result = Property_get_wrapModeU((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::TextureWrapMode(result);
}


void (*DotNet::UnityEngine::Texture2D::Property_set_wrapModeU)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void Texture2D::wrapModeU(::DotNet::UnityEngine::TextureWrapMode value) const {
    void* reinteropException = nullptr;
    Property_set_wrapModeU((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::UnityEngine::Texture2D::Property_get_wrapModeV)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::TextureWrapMode Texture2D::wrapModeV() const {
    void* reinteropException = nullptr;
    auto result = Property_get_wrapModeV((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::TextureWrapMode(result);
}


void (*DotNet::UnityEngine::Texture2D::Property_set_wrapModeV)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void Texture2D::wrapModeV(::DotNet::UnityEngine::TextureWrapMode value) const {
    void* reinteropException = nullptr;
    Property_set_wrapModeV((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::UnityEngine::Texture2D::Property_get_wrapModeW)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::TextureWrapMode Texture2D::wrapModeW() const {
    void* reinteropException = nullptr;
    auto result = Property_get_wrapModeW((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::TextureWrapMode(result);
}


void (*DotNet::UnityEngine::Texture2D::Property_set_wrapModeW)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void Texture2D::wrapModeW(::DotNet::UnityEngine::TextureWrapMode value) const {
    void* reinteropException = nullptr;
    Property_set_wrapModeW((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::UnityEngine::Texture2D::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String Texture2D::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Texture2D::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void Texture2D::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::UnityEngine::Texture2D::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> Texture2D::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::UnityEngine::Texture2D::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void Texture2D::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::UnityEngine::Texture2D::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool Texture2D::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool Texture2D::operator==(const Texture2D& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool Texture2D::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool Texture2D::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::UnityEngine::Texture2D::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool Texture2D::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool Texture2D::operator!=(const Texture2D& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool Texture2D::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool Texture2D::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::UnityEngine::Texture2D::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Texture2D::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::UnityEngine


