#include <DotNet/CesiumForUnity/CesiumPrimitiveFeatures.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/MonoBehaviour.h>
#include <DotNet/UnityEngine/Behaviour.h>
#include <DotNet/UnityEngine/Component.h>
#include <DotNet/UnityEngine/Object.h>
#include <DotNet/System/Object.h>
#include <DotNet/CesiumForUnity/CesiumFeatureIdSet.h>
#include <DotNet/System/Array1.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/Coroutine.h>
#include <DotNet/System/Collections/IEnumerator.h>
#include <cstdint>
#include <DotNet/UnityEngine/GameObject.h>
#include <DotNet/UnityEngine/Transform.h>
#include <DotNet/System/String.h>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>



namespace DotNet::CesiumForUnity {

CesiumPrimitiveFeatures::CesiumPrimitiveFeatures(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumPrimitiveFeatures::CesiumPrimitiveFeatures(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& CesiumPrimitiveFeatures::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumPrimitiveFeatures::GetHandle() {
    return this->_handle;
}


CesiumPrimitiveFeatures::operator ::DotNet::UnityEngine::MonoBehaviour() const {
    return ::DotNet::UnityEngine::MonoBehaviour(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumPrimitiveFeatures::operator ::DotNet::UnityEngine::Behaviour() const {
    return ::DotNet::UnityEngine::Behaviour(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumPrimitiveFeatures::operator ::DotNet::UnityEngine::Component() const {
    return ::DotNet::UnityEngine::Component(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumPrimitiveFeatures::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumPrimitiveFeatures::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Property_get_featureIdSets)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet> CesiumPrimitiveFeatures::featureIdSets() const {
    void* reinteropException = nullptr;
    auto result = Property_get_featureIdSets((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Property_set_featureIdSets)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumPrimitiveFeatures::featureIdSets(const ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet>& value) const {
    void* reinteropException = nullptr;
    Property_set_featureIdSets((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumPrimitiveFeatures::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw)(void* thiz, void* routine, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Coroutine CesiumPrimitiveFeatures::StartCoroutine(const ::DotNet::System::Collections::IEnumerator& routine) const {
    void* reinteropException = nullptr;
    auto result = CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw((*this).GetHandle().GetRaw(), routine.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Coroutine(::DotNet::Reinterop::ObjectHandle(result));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Property_get_enabled)(void* thiz, void** reinteropException) = nullptr;


bool CesiumPrimitiveFeatures::enabled() const {
    void* reinteropException = nullptr;
    auto result = Property_get_enabled((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Property_set_enabled)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumPrimitiveFeatures::enabled(bool value) const {
    void* reinteropException = nullptr;
    Property_set_enabled((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Property_get_gameObject)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::GameObject CesiumPrimitiveFeatures::gameObject() const {
    void* reinteropException = nullptr;
    auto result = Property_get_gameObject((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::GameObject(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Property_get_transform)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Transform CesiumPrimitiveFeatures::transform() const {
    void* reinteropException = nullptr;
    auto result = Property_get_transform((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Transform(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumPrimitiveFeatures::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures CesiumPrimitiveFeatures::GetComponent<::DotNet::CesiumForUnity::CesiumPrimitiveFeatures>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumPrimitiveFeatures::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumPrimitiveFeatures::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> CesiumPrimitiveFeatures::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void CesiumPrimitiveFeatures::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumPrimitiveFeatures::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool CesiumPrimitiveFeatures::operator==(const CesiumPrimitiveFeatures& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumPrimitiveFeatures::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumPrimitiveFeatures::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumPrimitiveFeatures::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumPrimitiveFeatures::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool CesiumPrimitiveFeatures::operator!=(const CesiumPrimitiveFeatures& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumPrimitiveFeatures::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumPrimitiveFeatures::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumPrimitiveFeatures::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumPrimitiveFeatures::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::CesiumForUnity


