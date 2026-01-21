#include <DotNet/CesiumForUnity/CesiumGlobeAnchor.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/MonoBehaviour.h>
#include <DotNet/UnityEngine/Behaviour.h>
#include <DotNet/UnityEngine/Component.h>
#include <DotNet/UnityEngine/Object.h>
#include <DotNet/System/Object.h>
#include <DotNet/Unity/Mathematics/double3.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>
#include <DotNet/Unity/Mathematics/double4x4.h>
#include <DotNet/CesiumForUnity/CesiumGeoreference.h>
#include <DotNet/UnityEngine/Vector3.h>
#include <DotNet/UnityEngine/Quaternion.h>
#include <optional>
#include <DotNet/UnityEngine/Coroutine.h>
#include <DotNet/System/Collections/IEnumerator.h>
#include <DotNet/UnityEngine/GameObject.h>
#include <DotNet/UnityEngine/Transform.h>
#include <DotNet/CesiumForUnity/CesiumPrimitiveFeatures.h>
#include <DotNet/System/String.h>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>
#include "CesiumGlobeAnchorImpl.h"
#include <DotNet/Reinterop/ReinteropException.h>
#include <utility>
#include <DotNet/Unity/Mathematics/quaternion.h>

namespace DotNet::Unity::Mathematics {
struct double3;
}
namespace DotNet::Unity::Mathematics {
struct double4x4;
}
namespace DotNet::UnityEngine {
struct Vector3;
}
namespace DotNet::UnityEngine {
struct Quaternion;
}

namespace DotNet::CesiumForUnity {

CesiumGlobeAnchor::CesiumGlobeAnchor(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumGlobeAnchor::CesiumGlobeAnchor(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& CesiumGlobeAnchor::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumGlobeAnchor::GetHandle() {
    return this->_handle;
}


CesiumGlobeAnchor::operator ::DotNet::UnityEngine::MonoBehaviour() const {
    return ::DotNet::UnityEngine::MonoBehaviour(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumGlobeAnchor::operator ::DotNet::UnityEngine::Behaviour() const {
    return ::DotNet::UnityEngine::Behaviour(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumGlobeAnchor::operator ::DotNet::UnityEngine::Component() const {
    return ::DotNet::UnityEngine::Component(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumGlobeAnchor::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumGlobeAnchor::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_get_positionGlobeFixed)(void* thiz, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::Unity::Mathematics::double3 CesiumGlobeAnchor::positionGlobeFixed() const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::double3 result;
    Property_get_positionGlobeFixed((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_set_positionGlobeFixed)(void* thiz, const ::DotNet::Unity::Mathematics::double3* value, void** reinteropException) = nullptr;


void CesiumGlobeAnchor::positionGlobeFixed(const ::DotNet::Unity::Mathematics::double3& value) const {
    void* reinteropException = nullptr;
    Property_set_positionGlobeFixed((*this).GetHandle().GetRaw(), &value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_get_detectTransformChanges)(void* thiz, void** reinteropException) = nullptr;


bool CesiumGlobeAnchor::detectTransformChanges() const {
    void* reinteropException = nullptr;
    auto result = Property_get_detectTransformChanges((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_set_detectTransformChanges)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumGlobeAnchor::detectTransformChanges(bool value) const {
    void* reinteropException = nullptr;
    Property_set_detectTransformChanges((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_get_adjustOrientationForGlobeWhenMoving)(void* thiz, void** reinteropException) = nullptr;


bool CesiumGlobeAnchor::adjustOrientationForGlobeWhenMoving() const {
    void* reinteropException = nullptr;
    auto result = Property_get_adjustOrientationForGlobeWhenMoving((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_set_adjustOrientationForGlobeWhenMoving)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumGlobeAnchor::adjustOrientationForGlobeWhenMoving(bool value) const {
    void* reinteropException = nullptr;
    Property_set_adjustOrientationForGlobeWhenMoving((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_get_longitudeLatitudeHeight)(void* thiz, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::Unity::Mathematics::double3 CesiumGlobeAnchor::longitudeLatitudeHeight() const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::double3 result;
    Property_get_longitudeLatitudeHeight((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_set_longitudeLatitudeHeight)(void* thiz, const ::DotNet::Unity::Mathematics::double3* value, void** reinteropException) = nullptr;


void CesiumGlobeAnchor::longitudeLatitudeHeight(const ::DotNet::Unity::Mathematics::double3& value) const {
    void* reinteropException = nullptr;
    Property_set_longitudeLatitudeHeight((*this).GetHandle().GetRaw(), &value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_get_localToGlobeFixedMatrix)(void* thiz, ::DotNet::Unity::Mathematics::double4x4* pReturnValue, void** reinteropException) = nullptr;


::DotNet::Unity::Mathematics::double4x4 CesiumGlobeAnchor::localToGlobeFixedMatrix() const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::double4x4 result;
    Property_get_localToGlobeFixedMatrix((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_set_localToGlobeFixedMatrix)(void* thiz, const ::DotNet::Unity::Mathematics::double4x4* value, void** reinteropException) = nullptr;


void CesiumGlobeAnchor::localToGlobeFixedMatrix(const ::DotNet::Unity::Mathematics::double4x4& value) const {
    void* reinteropException = nullptr;
    Property_set_localToGlobeFixedMatrix((*this).GetHandle().GetRaw(), &value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::CallUpdateGeoreferenceIfNecessary_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumGlobeAnchor::UpdateGeoreferenceIfNecessary() const {
    void* reinteropException = nullptr;
    CallUpdateGeoreferenceIfNecessary_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_get__georeference)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_set__georeference)(void* thiz, void* value, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumGeoreference CesiumGlobeAnchor::_georeference() const {
    void* reinteropException = nullptr;
    auto result = Field_get__georeference((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return ::DotNet::CesiumForUnity::CesiumGeoreference(::DotNet::Reinterop::ObjectHandle(result));
}


void CesiumGlobeAnchor::_georeference(const ::DotNet::CesiumForUnity::CesiumGeoreference& value) const {
    void* reinteropException = nullptr;
    Field_set__georeference((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_get__localToGlobeFixedMatrix)(void* thiz, ::DotNet::Unity::Mathematics::double4x4* pReturnValue, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_set__localToGlobeFixedMatrix)(void* thiz, const ::DotNet::Unity::Mathematics::double4x4* value, void** reinteropException) = nullptr;


::DotNet::Unity::Mathematics::double4x4 CesiumGlobeAnchor::_localToGlobeFixedMatrix() const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::double4x4 result;
    Field_get__localToGlobeFixedMatrix((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return result;
}


void CesiumGlobeAnchor::_localToGlobeFixedMatrix(const ::DotNet::Unity::Mathematics::double4x4& value) const {
    void* reinteropException = nullptr;
    Field_set__localToGlobeFixedMatrix((*this).GetHandle().GetRaw(), &value, &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_get__localToGlobeFixedMatrixIsValid)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_set__localToGlobeFixedMatrixIsValid)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


bool CesiumGlobeAnchor::_localToGlobeFixedMatrixIsValid() const {
    void* reinteropException = nullptr;
    auto result = Field_get__localToGlobeFixedMatrixIsValid((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return !!result;
}


void CesiumGlobeAnchor::_localToGlobeFixedMatrixIsValid(bool value) const {
    void* reinteropException = nullptr;
    Field_set__localToGlobeFixedMatrixIsValid((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_get__lastLocalsAreValid)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_set__lastLocalsAreValid)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


bool CesiumGlobeAnchor::_lastLocalsAreValid() const {
    void* reinteropException = nullptr;
    auto result = Field_get__lastLocalsAreValid((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return !!result;
}


void CesiumGlobeAnchor::_lastLocalsAreValid(bool value) const {
    void* reinteropException = nullptr;
    Field_set__lastLocalsAreValid((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_get__lastLocalPosition)(void* thiz, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_set__lastLocalPosition)(void* thiz, const ::DotNet::UnityEngine::Vector3* value, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Vector3 CesiumGlobeAnchor::_lastLocalPosition() const {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Vector3 result;
    Field_get__lastLocalPosition((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return result;
}


void CesiumGlobeAnchor::_lastLocalPosition(const ::DotNet::UnityEngine::Vector3& value) const {
    void* reinteropException = nullptr;
    Field_set__lastLocalPosition((*this).GetHandle().GetRaw(), &value, &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_get__lastLocalRotation)(void* thiz, ::DotNet::UnityEngine::Quaternion* pReturnValue, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_set__lastLocalRotation)(void* thiz, const ::DotNet::UnityEngine::Quaternion* value, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Quaternion CesiumGlobeAnchor::_lastLocalRotation() const {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Quaternion result;
    Field_get__lastLocalRotation((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return result;
}


void CesiumGlobeAnchor::_lastLocalRotation(const ::DotNet::UnityEngine::Quaternion& value) const {
    void* reinteropException = nullptr;
    Field_set__lastLocalRotation((*this).GetHandle().GetRaw(), &value, &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_get__lastLocalScale)(void* thiz, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_set__lastLocalScale)(void* thiz, const ::DotNet::UnityEngine::Vector3* value, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Vector3 CesiumGlobeAnchor::_lastLocalScale() const {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Vector3 result;
    Field_get__lastLocalScale((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return result;
}


void CesiumGlobeAnchor::_lastLocalScale(const ::DotNet::UnityEngine::Vector3& value) const {
    void* reinteropException = nullptr;
    Field_set__lastLocalScale((*this).GetHandle().GetRaw(), &value, &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_get__lastEllipsoidRadii)(void* thiz, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Field_set__lastEllipsoidRadii)(void* thiz, const ::DotNet::Unity::Mathematics::double3* value, void** reinteropException) = nullptr;


::std::optional<::DotNet::Unity::Mathematics::double3> CesiumGlobeAnchor::_lastEllipsoidRadii() const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::double3 result;
    std::uint8_t resultIsValid = Field_get__lastEllipsoidRadii((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


void CesiumGlobeAnchor::_lastEllipsoidRadii(const ::std::optional<::DotNet::Unity::Mathematics::double3>& value) const {
    void* reinteropException = nullptr;
    Field_set__lastEllipsoidRadii((*this).GetHandle().GetRaw(), value.has_value() ? &value.value() : nullptr, &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


void* (*DotNet::CesiumForUnity::CesiumGlobeAnchor::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw)(void* thiz, void* routine, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Coroutine CesiumGlobeAnchor::StartCoroutine(const ::DotNet::System::Collections::IEnumerator& routine) const {
    void* reinteropException = nullptr;
    auto result = CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw((*this).GetHandle().GetRaw(), routine.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Coroutine(::DotNet::Reinterop::ObjectHandle(result));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_get_enabled)(void* thiz, void** reinteropException) = nullptr;


bool CesiumGlobeAnchor::enabled() const {
    void* reinteropException = nullptr;
    auto result = Property_get_enabled((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_set_enabled)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumGlobeAnchor::enabled(bool value) const {
    void* reinteropException = nullptr;
    Property_set_enabled((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_get_gameObject)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::GameObject CesiumGlobeAnchor::gameObject() const {
    void* reinteropException = nullptr;
    auto result = Property_get_gameObject((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::GameObject(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_get_transform)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Transform CesiumGlobeAnchor::transform() const {
    void* reinteropException = nullptr;
    auto result = Property_get_transform((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Transform(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumGlobeAnchor::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures CesiumGlobeAnchor::GetComponent<::DotNet::CesiumForUnity::CesiumPrimitiveFeatures>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumGlobeAnchor::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumGlobeAnchor::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> CesiumGlobeAnchor::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void CesiumGlobeAnchor::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumGlobeAnchor::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool CesiumGlobeAnchor::operator==(const CesiumGlobeAnchor& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumGlobeAnchor::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumGlobeAnchor::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumGlobeAnchor::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumGlobeAnchor::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool CesiumGlobeAnchor::operator!=(const CesiumGlobeAnchor& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumGlobeAnchor::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumGlobeAnchor::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumGlobeAnchor::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumGlobeAnchor::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumGlobeAnchor_SetNewLocalToGlobeFixedMatrix(void* handle, const ::DotNet::Unity::Mathematics::double4x4* newLocalToGlobeFixedMatrix, void** reinteropException) {
  try {
    const ::DotNet::CesiumForUnity::CesiumGlobeAnchor wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    CesiumForUnityNative::CesiumGlobeAnchorImpl::SetNewLocalToGlobeFixedMatrix(wrapper, *newLocalToGlobeFixedMatrix);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumGlobeAnchor_SetNewLocalToGlobeFixedMatrixFromTransform(void* handle, void** reinteropException) {
  try {
    const ::DotNet::CesiumForUnity::CesiumGlobeAnchor wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    CesiumForUnityNative::CesiumGlobeAnchorImpl::SetNewLocalToGlobeFixedMatrixFromTransform(wrapper);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumGlobeAnchor_GetLocalToEastUpNorthRotation(void* handle, ::DotNet::Unity::Mathematics::quaternion* pReturnValue, void** reinteropException) {
  try {
    const ::DotNet::CesiumForUnity::CesiumGlobeAnchor wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = CesiumForUnityNative::CesiumGlobeAnchorImpl::GetLocalToEastUpNorthRotation(wrapper);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumGlobeAnchor_SetLocalToEastUpNorthRotation(void* handle, const ::DotNet::Unity::Mathematics::quaternion* newRotation, void** reinteropException) {
  try {
    const ::DotNet::CesiumForUnity::CesiumGlobeAnchor wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    CesiumForUnityNative::CesiumGlobeAnchorImpl::SetLocalToEastUpNorthRotation(wrapper, *newRotation);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}

} // extern "C"

