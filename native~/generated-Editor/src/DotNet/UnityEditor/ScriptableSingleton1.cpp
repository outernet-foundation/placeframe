#include <DotNet/CesiumForUnity/CesiumIonServerManager.h>
#include <DotNet/UnityEditor/ScriptableSingleton1.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/Object.h>
#include <DotNet/System/Object.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/String.h>
#include <cstdint>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>



namespace DotNet::UnityEditor {

ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::ScriptableSingleton1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::ScriptableSingleton1(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::GetHandle() {
    return this->_handle;
}


ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::UnityEditor::ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::Property_get_instance)(void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumIonServerManager ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::instance() {
    void* reinteropException = nullptr;
    auto result = Property_get_instance(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumIonServerManager(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEditor::ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEditor::ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::UnityEditor::ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::UnityEditor::ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::UnityEditor::ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::operator==(const ScriptableSingleton1& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::UnityEditor::ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::operator!=(const ScriptableSingleton1& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::UnityEditor::ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::UnityEditor


