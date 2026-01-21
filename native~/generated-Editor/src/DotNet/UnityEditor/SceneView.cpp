#include <DotNet/UnityEditor/SceneView.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEditor/EditorWindow.h>
#include <DotNet/UnityEngine/Object.h>
#include <DotNet/System/Object.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/Vector3.h>
#include <DotNet/UnityEngine/Quaternion.h>
#include <DotNet/UnityEngine/Camera.h>
#include <DotNet/System/String.h>
#include <cstdint>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>

namespace DotNet::UnityEngine {
struct Vector3;
}
namespace DotNet::UnityEngine {
struct Quaternion;
}

namespace DotNet::UnityEditor {

SceneView::SceneView(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


SceneView::SceneView(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& SceneView::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& SceneView::GetHandle() {
    return this->_handle;
}


SceneView::operator ::DotNet::UnityEditor::EditorWindow() const {
    return ::DotNet::UnityEditor::EditorWindow(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


SceneView::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


SceneView::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::UnityEditor::SceneView::Property_get_lastActiveSceneView)(void** reinteropException) = nullptr;


::DotNet::UnityEditor::SceneView SceneView::lastActiveSceneView() {
    void* reinteropException = nullptr;
    auto result = Property_get_lastActiveSceneView(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEditor::SceneView(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEditor::SceneView::Property_get_pivot)(void* thiz, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Vector3 SceneView::pivot() const {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Vector3 result;
    Property_get_pivot((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEditor::SceneView::Property_set_pivot)(void* thiz, const ::DotNet::UnityEngine::Vector3* value, void** reinteropException) = nullptr;


void SceneView::pivot(const ::DotNet::UnityEngine::Vector3& value) const {
    void* reinteropException = nullptr;
    Property_set_pivot((*this).GetHandle().GetRaw(), &value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEditor::SceneView::Property_get_rotation)(void* thiz, ::DotNet::UnityEngine::Quaternion* pReturnValue, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Quaternion SceneView::rotation() const {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Quaternion result;
    Property_get_rotation((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEditor::SceneView::Property_set_rotation)(void* thiz, const ::DotNet::UnityEngine::Quaternion* value, void** reinteropException) = nullptr;


void SceneView::rotation(const ::DotNet::UnityEngine::Quaternion& value) const {
    void* reinteropException = nullptr;
    Property_set_rotation((*this).GetHandle().GetRaw(), &value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::UnityEditor::SceneView::Property_get_camera)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Camera SceneView::camera() const {
    void* reinteropException = nullptr;
    auto result = Property_get_camera((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Camera(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEditor::SceneView::CallClose_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void SceneView::Close() const {
    void* reinteropException = nullptr;
    CallClose_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::UnityEditor::SceneView::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String SceneView::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEditor::SceneView::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void SceneView::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::UnityEditor::SceneView::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> SceneView::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::UnityEditor::SceneView::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void SceneView::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::UnityEditor::SceneView::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool SceneView::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool SceneView::operator==(const SceneView& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool SceneView::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool SceneView::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::UnityEditor::SceneView::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool SceneView::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool SceneView::operator!=(const SceneView& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool SceneView::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool SceneView::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::UnityEditor::SceneView::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t SceneView::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::UnityEditor


