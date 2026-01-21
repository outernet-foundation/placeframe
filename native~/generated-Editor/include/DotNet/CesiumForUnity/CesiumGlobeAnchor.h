#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Unity/Mathematics/double3.h>
#include <optional>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::UnityEngine {
class MonoBehaviour;
}
namespace DotNet::UnityEngine {
class Behaviour;
}
namespace DotNet::UnityEngine {
class Component;
}
namespace DotNet::UnityEngine {
class Object;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::Unity::Mathematics {
struct double3;
}
namespace DotNet::Unity::Mathematics {
struct double4x4;
}
namespace DotNet::CesiumForUnity {
class CesiumGeoreference;
}
namespace DotNet::UnityEngine {
struct Vector3;
}
namespace DotNet::UnityEngine {
struct Quaternion;
}
namespace DotNet::UnityEngine {
class Coroutine;
}
namespace DotNet::System::Collections {
class IEnumerator;
}
namespace DotNet::UnityEngine {
class GameObject;
}
namespace DotNet::UnityEngine {
class Transform;
}
namespace DotNet::System {
class String;
}
namespace DotNet::UnityEngine {
enum class HideFlags : uint32_t;
}

namespace DotNet::CesiumForUnity {

class CesiumGlobeAnchor {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumGlobeAnchor(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumGlobeAnchor(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::UnityEngine::MonoBehaviour() const;
  public: operator ::DotNet::UnityEngine::Behaviour() const;
  public: operator ::DotNet::UnityEngine::Component() const;
  public: operator ::DotNet::UnityEngine::Object() const;
  public: operator ::DotNet::System::Object() const;
  private: static void (*Property_get_positionGlobeFixed)(void* thiz, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException);
  public: ::DotNet::Unity::Mathematics::double3 positionGlobeFixed() const;
  private: static void (*Property_set_positionGlobeFixed)(void* thiz, const ::DotNet::Unity::Mathematics::double3* value, void** reinteropException);
  public: void positionGlobeFixed(const ::DotNet::Unity::Mathematics::double3& value) const;
  private: static ::std::uint8_t (*Property_get_detectTransformChanges)(void* thiz, void** reinteropException);
  public: bool detectTransformChanges() const;
  private: static void (*Property_set_detectTransformChanges)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void detectTransformChanges(bool value) const;
  private: static ::std::uint8_t (*Property_get_adjustOrientationForGlobeWhenMoving)(void* thiz, void** reinteropException);
  public: bool adjustOrientationForGlobeWhenMoving() const;
  private: static void (*Property_set_adjustOrientationForGlobeWhenMoving)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void adjustOrientationForGlobeWhenMoving(bool value) const;
  private: static void (*Property_get_longitudeLatitudeHeight)(void* thiz, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException);
  public: ::DotNet::Unity::Mathematics::double3 longitudeLatitudeHeight() const;
  private: static void (*Property_set_longitudeLatitudeHeight)(void* thiz, const ::DotNet::Unity::Mathematics::double3* value, void** reinteropException);
  public: void longitudeLatitudeHeight(const ::DotNet::Unity::Mathematics::double3& value) const;
  private: static void (*Property_get_localToGlobeFixedMatrix)(void* thiz, ::DotNet::Unity::Mathematics::double4x4* pReturnValue, void** reinteropException);
  public: ::DotNet::Unity::Mathematics::double4x4 localToGlobeFixedMatrix() const;
  private: static void (*Property_set_localToGlobeFixedMatrix)(void* thiz, const ::DotNet::Unity::Mathematics::double4x4* value, void** reinteropException);
  public: void localToGlobeFixedMatrix(const ::DotNet::Unity::Mathematics::double4x4& value) const;
  private: static void (*CallUpdateGeoreferenceIfNecessary_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void UpdateGeoreferenceIfNecessary() const;
  private: static void* (*Field_get__georeference)(void* thiz, void** reinteropException);
  private: static void (*Field_set__georeference)(void* thiz, void* value, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumGeoreference _georeference() const;
  public: void _georeference(const ::DotNet::CesiumForUnity::CesiumGeoreference& value) const;
  private: static void (*Field_get__localToGlobeFixedMatrix)(void* thiz, ::DotNet::Unity::Mathematics::double4x4* pReturnValue, void** reinteropException);
  private: static void (*Field_set__localToGlobeFixedMatrix)(void* thiz, const ::DotNet::Unity::Mathematics::double4x4* value, void** reinteropException);
  public: ::DotNet::Unity::Mathematics::double4x4 _localToGlobeFixedMatrix() const;
  public: void _localToGlobeFixedMatrix(const ::DotNet::Unity::Mathematics::double4x4& value) const;
  private: static ::std::uint8_t (*Field_get__localToGlobeFixedMatrixIsValid)(void* thiz, void** reinteropException);
  private: static void (*Field_set__localToGlobeFixedMatrixIsValid)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: bool _localToGlobeFixedMatrixIsValid() const;
  public: void _localToGlobeFixedMatrixIsValid(bool value) const;
  private: static ::std::uint8_t (*Field_get__lastLocalsAreValid)(void* thiz, void** reinteropException);
  private: static void (*Field_set__lastLocalsAreValid)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: bool _lastLocalsAreValid() const;
  public: void _lastLocalsAreValid(bool value) const;
  private: static void (*Field_get__lastLocalPosition)(void* thiz, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException);
  private: static void (*Field_set__lastLocalPosition)(void* thiz, const ::DotNet::UnityEngine::Vector3* value, void** reinteropException);
  public: ::DotNet::UnityEngine::Vector3 _lastLocalPosition() const;
  public: void _lastLocalPosition(const ::DotNet::UnityEngine::Vector3& value) const;
  private: static void (*Field_get__lastLocalRotation)(void* thiz, ::DotNet::UnityEngine::Quaternion* pReturnValue, void** reinteropException);
  private: static void (*Field_set__lastLocalRotation)(void* thiz, const ::DotNet::UnityEngine::Quaternion* value, void** reinteropException);
  public: ::DotNet::UnityEngine::Quaternion _lastLocalRotation() const;
  public: void _lastLocalRotation(const ::DotNet::UnityEngine::Quaternion& value) const;
  private: static void (*Field_get__lastLocalScale)(void* thiz, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException);
  private: static void (*Field_set__lastLocalScale)(void* thiz, const ::DotNet::UnityEngine::Vector3* value, void** reinteropException);
  public: ::DotNet::UnityEngine::Vector3 _lastLocalScale() const;
  public: void _lastLocalScale(const ::DotNet::UnityEngine::Vector3& value) const;
  private: static ::std::uint8_t (*Field_get__lastEllipsoidRadii)(void* thiz, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException);
  private: static void (*Field_set__lastEllipsoidRadii)(void* thiz, const ::DotNet::Unity::Mathematics::double3* value, void** reinteropException);
  public: ::std::optional<::DotNet::Unity::Mathematics::double3> _lastEllipsoidRadii() const;
  public: void _lastEllipsoidRadii(const ::std::optional<::DotNet::Unity::Mathematics::double3>& value) const;
  private: static void* (*CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw)(void* thiz, void* routine, void** reinteropException);
  public: ::DotNet::UnityEngine::Coroutine StartCoroutine(const ::DotNet::System::Collections::IEnumerator& routine) const;
  private: static ::std::uint8_t (*Property_get_enabled)(void* thiz, void** reinteropException);
  public: bool enabled() const;
  private: static void (*Property_set_enabled)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void enabled(bool value) const;
  private: static void* (*Property_get_gameObject)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::GameObject gameObject() const;
  private: static void* (*Property_get_transform)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::Transform transform() const;
  public: template <typename T>
  T GetComponent() const;
  private: static void* (*CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw)(void* thiz, void** reinteropException);
  private: static void* (*Property_get_name)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String name() const;
  private: static void (*Property_set_name)(void* thiz, void* value, void** reinteropException);
  public: void name(const ::DotNet::System::String& value) const;
  private: static ::std::uint32_t (*Property_get_hideFlags)(void* thiz, void** reinteropException);
  public: ::flags::flags<::DotNet::UnityEngine::HideFlags> hideFlags() const;
  private: static void (*Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: void hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const;
  private: static ::std::uint8_t (*Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator==(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator==(const CesiumGlobeAnchor& rhs) const;
  public: bool operator==(std::nullptr_t) const;
  private: static ::std::uint8_t (*Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator!=(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator!=(const CesiumGlobeAnchor& rhs) const;
  public: bool operator!=(std::nullptr_t) const;
  private: static ::std::int32_t (*CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::std::int32_t GetInstanceID() const;
};

} // namespace DotNet::CesiumForUnity


