#include <DotNet/CesiumForUnity/CesiumGeoreference.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/MonoBehaviour.h>
#include <DotNet/UnityEngine/Behaviour.h>
#include <DotNet/UnityEngine/Component.h>
#include <DotNet/UnityEngine/Object.h>
#include <DotNet/System/Object.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/CesiumGeoreferenceOriginPlacement.h>
#include <DotNet/CesiumForUnity/CesiumGeoreferenceOriginAuthority.h>
#include <DotNet/Unity/Mathematics/double4x4.h>
#include <DotNet/CesiumForUnity/CesiumEllipsoid.h>
#include <DotNet/System/Action.h>
#include <DotNet/UnityEngine/Coroutine.h>
#include <DotNet/System/Collections/IEnumerator.h>
#include <DotNet/UnityEngine/GameObject.h>
#include <DotNet/UnityEngine/Transform.h>
#include <DotNet/CesiumForUnity/CesiumPrimitiveFeatures.h>
#include <DotNet/System/String.h>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>
#include "CesiumGeoreferenceImpl.h"
#include <utility>
#include <DotNet/Reinterop/ReinteropException.h>



namespace DotNet::CesiumForUnity {

CesiumGeoreference::CesiumGeoreference(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumGeoreference::CesiumGeoreference(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& CesiumGeoreference::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumGeoreference::GetHandle() {
    return this->_handle;
}


CesiumGeoreference::operator ::DotNet::UnityEngine::MonoBehaviour() const {
    return ::DotNet::UnityEngine::MonoBehaviour(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumGeoreference::operator ::DotNet::UnityEngine::Behaviour() const {
    return ::DotNet::UnityEngine::Behaviour(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumGeoreference::operator ::DotNet::UnityEngine::Component() const {
    return ::DotNet::UnityEngine::Component(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumGeoreference::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumGeoreference::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


double (*DotNet::CesiumForUnity::CesiumGeoreference::Property_get_longitude)(void* thiz, void** reinteropException) = nullptr;


double CesiumGeoreference::longitude() const {
    void* reinteropException = nullptr;
    auto result = Property_get_longitude((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumGeoreference::Property_set_longitude)(void* thiz, double value, void** reinteropException) = nullptr;


void CesiumGeoreference::longitude(double value) const {
    void* reinteropException = nullptr;
    Property_set_longitude((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


double (*DotNet::CesiumForUnity::CesiumGeoreference::Property_get_latitude)(void* thiz, void** reinteropException) = nullptr;


double CesiumGeoreference::latitude() const {
    void* reinteropException = nullptr;
    auto result = Property_get_latitude((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumGeoreference::Property_set_latitude)(void* thiz, double value, void** reinteropException) = nullptr;


void CesiumGeoreference::latitude(double value) const {
    void* reinteropException = nullptr;
    Property_set_latitude((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


double (*DotNet::CesiumForUnity::CesiumGeoreference::Property_get_height)(void* thiz, void** reinteropException) = nullptr;


double CesiumGeoreference::height() const {
    void* reinteropException = nullptr;
    auto result = Property_get_height((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumGeoreference::Property_set_height)(void* thiz, double value, void** reinteropException) = nullptr;


void CesiumGeoreference::height(double value) const {
    void* reinteropException = nullptr;
    Property_set_height((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


double (*DotNet::CesiumForUnity::CesiumGeoreference::Property_get_ecefX)(void* thiz, void** reinteropException) = nullptr;


double CesiumGeoreference::ecefX() const {
    void* reinteropException = nullptr;
    auto result = Property_get_ecefX((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumGeoreference::Property_set_ecefX)(void* thiz, double value, void** reinteropException) = nullptr;


void CesiumGeoreference::ecefX(double value) const {
    void* reinteropException = nullptr;
    Property_set_ecefX((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


double (*DotNet::CesiumForUnity::CesiumGeoreference::Property_get_ecefY)(void* thiz, void** reinteropException) = nullptr;


double CesiumGeoreference::ecefY() const {
    void* reinteropException = nullptr;
    auto result = Property_get_ecefY((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumGeoreference::Property_set_ecefY)(void* thiz, double value, void** reinteropException) = nullptr;


void CesiumGeoreference::ecefY(double value) const {
    void* reinteropException = nullptr;
    Property_set_ecefY((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


double (*DotNet::CesiumForUnity::CesiumGeoreference::Property_get_ecefZ)(void* thiz, void** reinteropException) = nullptr;


double CesiumGeoreference::ecefZ() const {
    void* reinteropException = nullptr;
    auto result = Property_get_ecefZ((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumGeoreference::Property_set_ecefZ)(void* thiz, double value, void** reinteropException) = nullptr;


void CesiumGeoreference::ecefZ(double value) const {
    void* reinteropException = nullptr;
    Property_set_ecefZ((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumGeoreference::Property_get_originPlacement)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumGeoreferenceOriginPlacement CesiumGeoreference::originPlacement() const {
    void* reinteropException = nullptr;
    auto result = Property_get_originPlacement((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumGeoreferenceOriginPlacement(result);
}


void (*DotNet::CesiumForUnity::CesiumGeoreference::Property_set_originPlacement)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void CesiumGeoreference::originPlacement(::DotNet::CesiumForUnity::CesiumGeoreferenceOriginPlacement value) const {
    void* reinteropException = nullptr;
    Property_set_originPlacement((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumGeoreference::Property_get_originAuthority)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumGeoreferenceOriginAuthority CesiumGeoreference::originAuthority() const {
    void* reinteropException = nullptr;
    auto result = Property_get_originAuthority((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumGeoreferenceOriginAuthority(result);
}


void (*DotNet::CesiumForUnity::CesiumGeoreference::Property_set_originAuthority)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void CesiumGeoreference::originAuthority(::DotNet::CesiumForUnity::CesiumGeoreferenceOriginAuthority value) const {
    void* reinteropException = nullptr;
    Property_set_originAuthority((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


double (*DotNet::CesiumForUnity::CesiumGeoreference::Property_get_scale)(void* thiz, void** reinteropException) = nullptr;


double CesiumGeoreference::scale() const {
    void* reinteropException = nullptr;
    auto result = Property_get_scale((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumGeoreference::Property_set_scale)(void* thiz, double value, void** reinteropException) = nullptr;


void CesiumGeoreference::scale(double value) const {
    void* reinteropException = nullptr;
    Property_set_scale((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumGeoreference::Property_get_ecefToLocalMatrix)(void* thiz, ::DotNet::Unity::Mathematics::double4x4* pReturnValue, void** reinteropException) = nullptr;


::DotNet::Unity::Mathematics::double4x4 CesiumGeoreference::ecefToLocalMatrix() const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::double4x4 result;
    Property_get_ecefToLocalMatrix((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*DotNet::CesiumForUnity::CesiumGeoreference::Property_get_ellipsoid)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumEllipsoid CesiumGeoreference::ellipsoid() const {
    void* reinteropException = nullptr;
    auto result = Property_get_ellipsoid((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumEllipsoid(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumGeoreference::Property_set_ellipsoid)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumGeoreference::ellipsoid(const ::DotNet::CesiumForUnity::CesiumEllipsoid& value) const {
    void* reinteropException = nullptr;
    Property_set_ellipsoid((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumGeoreference::CallMoveOrigin_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumGeoreference::MoveOrigin() const {
    void* reinteropException = nullptr;
    CallMoveOrigin_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumGeoreference::Calladd_changed_lHaT5LN6vSYwmLLE2__7bOw)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumGeoreference::add_changed(const ::DotNet::System::Action& value) const {
    void* reinteropException = nullptr;
    Calladd_changed_lHaT5LN6vSYwmLLE2__7bOw((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumGeoreference::Callremove_changed_lHaT5LN6vSYwmLLE2__7bOw)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumGeoreference::remove_changed(const ::DotNet::System::Action& value) const {
    void* reinteropException = nullptr;
    Callremove_changed_lHaT5LN6vSYwmLLE2__7bOw((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumGeoreference::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw)(void* thiz, void* routine, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Coroutine CesiumGeoreference::StartCoroutine(const ::DotNet::System::Collections::IEnumerator& routine) const {
    void* reinteropException = nullptr;
    auto result = CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw((*this).GetHandle().GetRaw(), routine.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Coroutine(::DotNet::Reinterop::ObjectHandle(result));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumGeoreference::Property_get_enabled)(void* thiz, void** reinteropException) = nullptr;


bool CesiumGeoreference::enabled() const {
    void* reinteropException = nullptr;
    auto result = Property_get_enabled((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumGeoreference::Property_set_enabled)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumGeoreference::enabled(bool value) const {
    void* reinteropException = nullptr;
    Property_set_enabled((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumGeoreference::Property_get_gameObject)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::GameObject CesiumGeoreference::gameObject() const {
    void* reinteropException = nullptr;
    auto result = Property_get_gameObject((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::GameObject(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumGeoreference::Property_get_transform)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Transform CesiumGeoreference::transform() const {
    void* reinteropException = nullptr;
    auto result = Property_get_transform((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Transform(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumGeoreference::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures CesiumGeoreference::GetComponent<::DotNet::CesiumForUnity::CesiumPrimitiveFeatures>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumGeoreference::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumGeoreference::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumGeoreference::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumGeoreference::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumGeoreference::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> CesiumGeoreference::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::CesiumForUnity::CesiumGeoreference::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void CesiumGeoreference::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumGeoreference::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumGeoreference::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool CesiumGeoreference::operator==(const CesiumGeoreference& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumGeoreference::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumGeoreference::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumGeoreference::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumGeoreference::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool CesiumGeoreference::operator!=(const CesiumGeoreference& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumGeoreference::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumGeoreference::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumGeoreference::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumGeoreference::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*CesiumGeoreference::Property_get_NativeImplementation)(void*) = nullptr;


::CesiumForUnityNative::CesiumGeoreferenceImpl& CesiumGeoreference::NativeImplementation() const noexcept {
  return *reinterpret_cast<::CesiumForUnityNative::CesiumGeoreferenceImpl*>(Property_get_NativeImplementation(this->_handle.GetRaw()));
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_CesiumGeoreference_CreateImplementation(void* handle) {
  const ::DotNet::CesiumForUnity::CesiumGeoreference wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
  auto pImpl = new CesiumForUnityNative::CesiumGeoreferenceImpl(wrapper);
  pImpl->addReference();
  return reinterpret_cast<void*>(pImpl);
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumGeoreference_DestroyImplementation(void* pImpl) {
  auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumGeoreferenceImpl*>(pImpl);
  if (pImplTyped) pImplTyped->releaseReference();
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumGeoreference_ComputeLocalToEarthCenteredEarthFixedTransformation(void* handle, void* pImpl, ::DotNet::Unity::Mathematics::double4x4* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumGeoreferenceImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumGeoreference wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->ComputeLocalToEarthCenteredEarthFixedTransformation(wrapper);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}

} // extern "C"

