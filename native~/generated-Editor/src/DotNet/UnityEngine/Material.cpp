#include <DotNet/UnityEngine/Material.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/Object.h>
#include <DotNet/System/Object.h>
#include <DotNet/System/String.h>
#include <DotNet/System/Array1.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/Shader.h>
#include <cstdint>
#include <DotNet/UnityEngine/Texture.h>
#include <DotNet/UnityEngine/Vector4.h>
#include <DotNet/UnityEngine/Vector2.h>
#include <DotNet/System/Collections/Generic/List1.h>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>

namespace DotNet::UnityEngine {
struct Vector4;
}
namespace DotNet::UnityEngine {
struct Vector2;
}

namespace DotNet::UnityEngine {

Material::Material(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Material::Material(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& Material::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Material::GetHandle() {
    return this->_handle;
}


Material::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Material::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::UnityEngine::Material::Property_get_shaderKeywords)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Array1<::DotNet::System::String> Material::shaderKeywords() const {
    void* reinteropException = nullptr;
    auto result = Property_get_shaderKeywords((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Array1<::DotNet::System::String>(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Material::Property_set_shaderKeywords)(void* thiz, void* value, void** reinteropException) = nullptr;


void Material::shaderKeywords(const ::DotNet::System::Array1<::DotNet::System::String>& value) const {
    void* reinteropException = nullptr;
    Property_set_shaderKeywords((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::UnityEngine::Material::Property_get_shader)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Shader Material::shader() const {
    void* reinteropException = nullptr;
    auto result = Property_get_shader((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Shader(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Material::Property_set_shader)(void* thiz, void* value, void** reinteropException) = nullptr;


void Material::shader(const ::DotNet::UnityEngine::Shader& value) const {
    void* reinteropException = nullptr;
    Property_set_shader((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::UnityEngine::Material::CallComputeCRC_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Material::ComputeCRC() const {
    void* reinteropException = nullptr;
    auto result = CallComputeCRC_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::Material::CallSetTexture_RautZzWeb93ejEP2lTHyaQ)(void* thiz, ::std::int32_t nameID, void* value, void** reinteropException) = nullptr;


void Material::SetTexture(::std::int32_t nameID, const ::DotNet::UnityEngine::Texture& value) const {
    void* reinteropException = nullptr;
    CallSetTexture_RautZzWeb93ejEP2lTHyaQ((*this).GetHandle().GetRaw(), nameID, value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Material::CallSetFloat_D__nDm70ZmOnS4ff1jXmV2g)(void* thiz, ::std::int32_t nameID, float value, void** reinteropException) = nullptr;


void Material::SetFloat(::std::int32_t nameID, float value) const {
    void* reinteropException = nullptr;
    CallSetFloat_D__nDm70ZmOnS4ff1jXmV2g((*this).GetHandle().GetRaw(), nameID, value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Material::CallSetVector_O_6hMsPoe8Mxh6B7ktm1dw)(void* thiz, ::std::int32_t nameID, const ::DotNet::UnityEngine::Vector4* value, void** reinteropException) = nullptr;


void Material::SetVector(::std::int32_t nameID, const ::DotNet::UnityEngine::Vector4& value) const {
    void* reinteropException = nullptr;
    CallSetVector_O_6hMsPoe8Mxh6B7ktm1dw((*this).GetHandle().GetRaw(), nameID, &value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Material::CallDisableKeyword_OjhTXlNYqXjpgz6Nd_41__A)(void* thiz, void* keyword, void** reinteropException) = nullptr;


void Material::DisableKeyword(const ::DotNet::System::String& keyword) const {
    void* reinteropException = nullptr;
    CallDisableKeyword_OjhTXlNYqXjpgz6Nd_41__A((*this).GetHandle().GetRaw(), keyword.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Material::CallEnableKeyword_OjhTXlNYqXjpgz6Nd_41__A)(void* thiz, void* keyword, void** reinteropException) = nullptr;


void Material::EnableKeyword(const ::DotNet::System::String& keyword) const {
    void* reinteropException = nullptr;
    CallEnableKeyword_OjhTXlNYqXjpgz6Nd_41__A((*this).GetHandle().GetRaw(), keyword.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::UnityEngine::Material::CallGetTexture_FH4N7HzmeU2VNRINVzNxBQ)(void* thiz, ::std::int32_t nameID, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Texture Material::GetTexture(::std::int32_t nameID) const {
    void* reinteropException = nullptr;
    auto result = CallGetTexture_FH4N7HzmeU2VNRINVzNxBQ((*this).GetHandle().GetRaw(), nameID, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Texture(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Material::CallSetTextureOffset_ZCDR2hJmAGOF0Xsc__aBBJA)(void* thiz, ::std::int32_t nameID, const ::DotNet::UnityEngine::Vector2* value, void** reinteropException) = nullptr;


void Material::SetTextureOffset(::std::int32_t nameID, const ::DotNet::UnityEngine::Vector2& value) const {
    void* reinteropException = nullptr;
    CallSetTextureOffset_ZCDR2hJmAGOF0Xsc__aBBJA((*this).GetHandle().GetRaw(), nameID, &value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Material::CallSetTextureScale_ZCDR2hJmAGOF0Xsc__aBBJA)(void* thiz, ::std::int32_t nameID, const ::DotNet::UnityEngine::Vector2* value, void** reinteropException) = nullptr;


void Material::SetTextureScale(::std::int32_t nameID, const ::DotNet::UnityEngine::Vector2& value) const {
    void* reinteropException = nullptr;
    CallSetTextureScale_ZCDR2hJmAGOF0Xsc__aBBJA((*this).GetHandle().GetRaw(), nameID, &value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Material::CallGetTexturePropertyNameIDs_HlbsadfaizcXlyyoqQEA3Q)(void* thiz, void* outNames, void** reinteropException) = nullptr;


void Material::GetTexturePropertyNameIDs(const ::DotNet::System::Collections::Generic::List1<::std::int32_t>& outNames) const {
    void* reinteropException = nullptr;
    CallGetTexturePropertyNameIDs_HlbsadfaizcXlyyoqQEA3Q((*this).GetHandle().GetRaw(), outNames.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::UnityEngine::Material::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String Material::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Material::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void Material::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::UnityEngine::Material::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> Material::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::UnityEngine::Material::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void Material::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::UnityEngine::Material::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool Material::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool Material::operator==(const Material& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool Material::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool Material::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::UnityEngine::Material::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool Material::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool Material::operator!=(const Material& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool Material::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool Material::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::UnityEngine::Material::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Material::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::UnityEngine


