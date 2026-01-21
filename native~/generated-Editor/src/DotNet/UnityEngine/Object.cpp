#include <DotNet/UnityEngine/Object.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/System/String.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>
#include <DotNet/CesiumForUnity/Cesium3DTileset.h>
#include <DotNet/System/Array1.h>
#include <DotNet/UnityEngine/Material.h>
#include <DotNet/UnityEngine/GameObject.h>



namespace DotNet::UnityEngine {

Object::Object(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Object::Object(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& Object::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Object::GetHandle() {
    return this->_handle;
}


Object::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::UnityEngine::Object::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String Object::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Object::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void Object::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::UnityEngine::Object::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> Object::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::UnityEngine::Object::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void Object::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::UnityEngine::Object::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool Object::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool Object::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::UnityEngine::Object::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool Object::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool Object::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void* (*DotNet::UnityEngine::Object::CallFindObjectsOfType_0EgxpGTzCG1YTfWqwgLniw)(void** reinteropException) = nullptr;


template <> ::DotNet::System::Array1<::DotNet::CesiumForUnity::Cesium3DTileset> Object::FindObjectsOfType<::DotNet::CesiumForUnity::Cesium3DTileset>() {
    void* reinteropException = nullptr;
    auto result = CallFindObjectsOfType_0EgxpGTzCG1YTfWqwgLniw(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Array1<::DotNet::CesiumForUnity::Cesium3DTileset>(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Object::CallDestroyImmediate_c5oFMRh3nzKMIo8On83YBg)(void* obj, ::std::uint8_t allowDestroyingAssets, void** reinteropException) = nullptr;


void Object::DestroyImmediate(const ::DotNet::UnityEngine::Object& obj, bool allowDestroyingAssets) {
    void* reinteropException = nullptr;
    CallDestroyImmediate_c5oFMRh3nzKMIo8On83YBg(obj.GetHandle().GetRaw(), allowDestroyingAssets ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Object::CallDestroyImmediate_x7aQMuJcEpatC9689ghI4A)(void* obj, void** reinteropException) = nullptr;


void Object::DestroyImmediate(const ::DotNet::UnityEngine::Object& obj) {
    void* reinteropException = nullptr;
    CallDestroyImmediate_x7aQMuJcEpatC9689ghI4A(obj.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::UnityEngine::Object::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Object::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*DotNet::UnityEngine::Object::CallInstantiate_zoaJbce7UThbChk6y9FLqQ)(void* original, void** reinteropException) = nullptr;


template <> ::DotNet::UnityEngine::Material Object::Instantiate<::DotNet::UnityEngine::Material>(const ::DotNet::UnityEngine::Material& original) {
    void* reinteropException = nullptr;
    auto result = CallInstantiate_zoaJbce7UThbChk6y9FLqQ(original.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Material(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Object::CallDestroy_x7aQMuJcEpatC9689ghI4A)(void* obj, void** reinteropException) = nullptr;


void Object::Destroy(const ::DotNet::UnityEngine::Object& obj) {
    void* reinteropException = nullptr;
    CallDestroy_x7aQMuJcEpatC9689ghI4A(obj.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::UnityEngine::Object::CallInstantiate_FQyuyLH6iz8rpKkiJwlxBA)(void* original, void** reinteropException) = nullptr;


template <> ::DotNet::UnityEngine::GameObject Object::Instantiate<::DotNet::UnityEngine::GameObject>(const ::DotNet::UnityEngine::GameObject& original) {
    void* reinteropException = nullptr;
    auto result = CallInstantiate_FQyuyLH6iz8rpKkiJwlxBA(original.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::GameObject(::DotNet::Reinterop::ObjectHandle(result));
}


} // namespace DotNet::UnityEngine


