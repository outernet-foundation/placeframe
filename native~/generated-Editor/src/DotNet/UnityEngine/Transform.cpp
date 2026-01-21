#include <DotNet/UnityEngine/Transform.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/Component.h>
#include <DotNet/UnityEngine/Object.h>
#include <DotNet/System/Object.h>
#include <DotNet/UnityEngine/Vector3.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/Quaternion.h>
#include <DotNet/UnityEngine/Matrix4x4.h>
#include <cstdint>
#include <DotNet/System/String.h>
#include <DotNet/UnityEngine/GameObject.h>
#include <DotNet/CesiumForUnity/CesiumPrimitiveFeatures.h>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>

namespace DotNet::UnityEngine {
struct Vector3;
}
namespace DotNet::UnityEngine {
struct Quaternion;
}

namespace DotNet::UnityEngine {

Transform::Transform(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Transform::Transform(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& Transform::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Transform::GetHandle() {
    return this->_handle;
}


Transform::operator ::DotNet::UnityEngine::Component() const {
    return ::DotNet::UnityEngine::Component(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Transform::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Transform::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::UnityEngine::Transform::Property_get_up)(void* thiz, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Vector3 Transform::up() const {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Vector3 result;
    Property_get_up((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::Transform::Property_set_up)(void* thiz, const ::DotNet::UnityEngine::Vector3* value, void** reinteropException) = nullptr;


void Transform::up(const ::DotNet::UnityEngine::Vector3& value) const {
    void* reinteropException = nullptr;
    Property_set_up((*this).GetHandle().GetRaw(), &value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Transform::Property_get_forward)(void* thiz, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Vector3 Transform::forward() const {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Vector3 result;
    Property_get_forward((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::Transform::Property_set_forward)(void* thiz, const ::DotNet::UnityEngine::Vector3* value, void** reinteropException) = nullptr;


void Transform::forward(const ::DotNet::UnityEngine::Vector3& value) const {
    void* reinteropException = nullptr;
    Property_set_forward((*this).GetHandle().GetRaw(), &value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Transform::Property_get_position)(void* thiz, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Vector3 Transform::position() const {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Vector3 result;
    Property_get_position((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::Transform::Property_set_position)(void* thiz, const ::DotNet::UnityEngine::Vector3* value, void** reinteropException) = nullptr;


void Transform::position(const ::DotNet::UnityEngine::Vector3& value) const {
    void* reinteropException = nullptr;
    Property_set_position((*this).GetHandle().GetRaw(), &value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::UnityEngine::Transform::Property_get_parent)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Transform Transform::parent() const {
    void* reinteropException = nullptr;
    auto result = Property_get_parent((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Transform(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Transform::Property_set_parent)(void* thiz, void* value, void** reinteropException) = nullptr;


void Transform::parent(const ::DotNet::UnityEngine::Transform& value) const {
    void* reinteropException = nullptr;
    Property_set_parent((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Transform::Property_get_rotation)(void* thiz, ::DotNet::UnityEngine::Quaternion* pReturnValue, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Quaternion Transform::rotation() const {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Quaternion result;
    Property_get_rotation((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::Transform::Property_set_rotation)(void* thiz, const ::DotNet::UnityEngine::Quaternion* value, void** reinteropException) = nullptr;


void Transform::rotation(const ::DotNet::UnityEngine::Quaternion& value) const {
    void* reinteropException = nullptr;
    Property_set_rotation((*this).GetHandle().GetRaw(), &value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Transform::Property_get_localPosition)(void* thiz, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Vector3 Transform::localPosition() const {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Vector3 result;
    Property_get_localPosition((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::Transform::Property_set_localPosition)(void* thiz, const ::DotNet::UnityEngine::Vector3* value, void** reinteropException) = nullptr;


void Transform::localPosition(const ::DotNet::UnityEngine::Vector3& value) const {
    void* reinteropException = nullptr;
    Property_set_localPosition((*this).GetHandle().GetRaw(), &value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Transform::Property_get_localRotation)(void* thiz, ::DotNet::UnityEngine::Quaternion* pReturnValue, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Quaternion Transform::localRotation() const {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Quaternion result;
    Property_get_localRotation((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::Transform::Property_set_localRotation)(void* thiz, const ::DotNet::UnityEngine::Quaternion* value, void** reinteropException) = nullptr;


void Transform::localRotation(const ::DotNet::UnityEngine::Quaternion& value) const {
    void* reinteropException = nullptr;
    Property_set_localRotation((*this).GetHandle().GetRaw(), &value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Transform::Property_get_localScale)(void* thiz, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Vector3 Transform::localScale() const {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Vector3 result;
    Property_get_localScale((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::Transform::Property_set_localScale)(void* thiz, const ::DotNet::UnityEngine::Vector3* value, void** reinteropException) = nullptr;


void Transform::localScale(const ::DotNet::UnityEngine::Vector3& value) const {
    void* reinteropException = nullptr;
    Property_set_localScale((*this).GetHandle().GetRaw(), &value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::UnityEngine::Transform::Property_get_root)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Transform Transform::root() const {
    void* reinteropException = nullptr;
    auto result = Property_get_root((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Transform(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Transform::Property_get_localToWorldMatrix)(void* thiz, ::DotNet::UnityEngine::Matrix4x4* pReturnValue, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Matrix4x4 Transform::localToWorldMatrix() const {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Matrix4x4 result;
    Property_get_localToWorldMatrix((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::Transform::Property_get_worldToLocalMatrix)(void* thiz, ::DotNet::UnityEngine::Matrix4x4* pReturnValue, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Matrix4x4 Transform::worldToLocalMatrix() const {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Matrix4x4 result;
    Property_get_worldToLocalMatrix((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::int32_t (*DotNet::UnityEngine::Transform::Property_get_childCount)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Transform::childCount() const {
    void* reinteropException = nullptr;
    auto result = Property_get_childCount((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::Transform::CallSetParent_hgOrrPUZTaGMovRxlX__YuA)(void* thiz, void* parent, ::std::uint8_t worldPositionStays, void** reinteropException) = nullptr;


void Transform::SetParent(const ::DotNet::UnityEngine::Transform& parent, bool worldPositionStays) const {
    void* reinteropException = nullptr;
    CallSetParent_hgOrrPUZTaGMovRxlX__YuA((*this).GetHandle().GetRaw(), parent.GetHandle().GetRaw(), worldPositionStays ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Transform::CallSetPositionAndRotation_4iSLIQZf65unfXZMWTVccw)(void* thiz, const ::DotNet::UnityEngine::Vector3* position, const ::DotNet::UnityEngine::Quaternion* rotation, void** reinteropException) = nullptr;


void Transform::SetPositionAndRotation(const ::DotNet::UnityEngine::Vector3& position, const ::DotNet::UnityEngine::Quaternion& rotation) const {
    void* reinteropException = nullptr;
    CallSetPositionAndRotation_4iSLIQZf65unfXZMWTVccw((*this).GetHandle().GetRaw(), &position, &rotation, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::UnityEngine::Transform::CallGetSiblingIndex_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Transform::GetSiblingIndex() const {
    void* reinteropException = nullptr;
    auto result = CallGetSiblingIndex_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*DotNet::UnityEngine::Transform::CallFind_huUPHg6iWoosrHfTvsoHeg)(void* thiz, void* n, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Transform Transform::Find(const ::DotNet::System::String& n) const {
    void* reinteropException = nullptr;
    auto result = CallFind_huUPHg6iWoosrHfTvsoHeg((*this).GetHandle().GetRaw(), n.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Transform(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::Transform::CallGetChild_7IHapUgMd7RT8__gH__cKUrw)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Transform Transform::GetChild(::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = CallGetChild_7IHapUgMd7RT8__gH__cKUrw((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Transform(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Transform::CallDetachChildren_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void Transform::DetachChildren() const {
    void* reinteropException = nullptr;
    CallDetachChildren_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::UnityEngine::Transform::Property_get_gameObject)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::GameObject Transform::gameObject() const {
    void* reinteropException = nullptr;
    auto result = Property_get_gameObject((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::GameObject(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::Transform::Property_get_transform)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Transform Transform::transform() const {
    void* reinteropException = nullptr;
    auto result = Property_get_transform((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Transform(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::Transform::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures Transform::GetComponent<::DotNet::CesiumForUnity::CesiumPrimitiveFeatures>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::Transform::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String Transform::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Transform::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void Transform::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::UnityEngine::Transform::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> Transform::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::UnityEngine::Transform::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void Transform::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::UnityEngine::Transform::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool Transform::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool Transform::operator==(const Transform& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool Transform::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool Transform::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::UnityEngine::Transform::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool Transform::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool Transform::operator!=(const Transform& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool Transform::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool Transform::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::UnityEngine::Transform::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Transform::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::UnityEngine


