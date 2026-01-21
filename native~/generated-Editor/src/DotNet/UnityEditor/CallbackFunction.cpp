#include <DotNet/UnityEditor/CallbackFunction.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/MulticastDelegate.h>
#include <DotNet/System/Delegate.h>
#include <DotNet/System/Object.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropException.h>
#include <DotNet/System/String.h>



namespace DotNet::UnityEditor {

CallbackFunction::CallbackFunction(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CallbackFunction::CallbackFunction(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& CallbackFunction::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CallbackFunction::GetHandle() {
    return this->_handle;
}


CallbackFunction::operator ::DotNet::System::MulticastDelegate() const {
    return ::DotNet::System::MulticastDelegate(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CallbackFunction::operator ::DotNet::System::Delegate() const {
    return ::DotNet::System::Delegate(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CallbackFunction::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::UnityEditor::CallbackFunction::CallInvoke_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CallbackFunction::Invoke() const {
    void* reinteropException = nullptr;
    CallInvoke_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::UnityEditor::CallbackFunction::Callop_Equality__iYzpyUo7S__gDd8L5jFzrg)(void* d1, void* d2, void** reinteropException) = nullptr;


bool CallbackFunction::operator==(const ::DotNet::System::MulticastDelegate& rhs) const {
  return op_Equality(*this, rhs);
}


bool CallbackFunction::operator==(const CallbackFunction& rhs) const {
return op_Equality(*this, ::DotNet::System::MulticastDelegate(rhs));
}


bool CallbackFunction::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::System::MulticastDelegate(nullptr));
}


bool CallbackFunction::op_Equality(const ::DotNet::System::MulticastDelegate& d1, const ::DotNet::System::MulticastDelegate& d2) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality__iYzpyUo7S__gDd8L5jFzrg(d1.GetHandle().GetRaw(), d2.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::UnityEditor::CallbackFunction::Callop_Inequality__iYzpyUo7S__gDd8L5jFzrg)(void* d1, void* d2, void** reinteropException) = nullptr;


bool CallbackFunction::operator!=(const ::DotNet::System::MulticastDelegate& rhs) const {
  return op_Inequality(*this, rhs);
}


bool CallbackFunction::operator!=(const CallbackFunction& rhs) const {
return op_Inequality(*this, ::DotNet::System::MulticastDelegate(rhs));
}


bool CallbackFunction::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::System::MulticastDelegate(nullptr));
}


bool CallbackFunction::op_Inequality(const ::DotNet::System::MulticastDelegate& d1, const ::DotNet::System::MulticastDelegate& d2) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality__iYzpyUo7S__gDd8L5jFzrg(d1.GetHandle().GetRaw(), d2.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::UnityEditor::CallbackFunction::Callop_Equality_a0RmOPC1vpOfulhhfnafBA)(void* d1, void* d2, void** reinteropException) = nullptr;


bool CallbackFunction::operator==(const ::DotNet::System::Delegate& rhs) const {
  return op_Equality(*this, rhs);
}


bool CallbackFunction::op_Equality(const ::DotNet::System::Delegate& d1, const ::DotNet::System::Delegate& d2) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_a0RmOPC1vpOfulhhfnafBA(d1.GetHandle().GetRaw(), d2.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::UnityEditor::CallbackFunction::Callop_Inequality_a0RmOPC1vpOfulhhfnafBA)(void* d1, void* d2, void** reinteropException) = nullptr;


bool CallbackFunction::operator!=(const ::DotNet::System::Delegate& rhs) const {
  return op_Inequality(*this, rhs);
}


bool CallbackFunction::op_Inequality(const ::DotNet::System::Delegate& d1, const ::DotNet::System::Delegate& d2) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_a0RmOPC1vpOfulhhfnafBA(d1.GetHandle().GetRaw(), d2.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void* (*CallbackFunction::CreateDelegate)(void* pCallbackFunction) = nullptr;


CallbackFunction::CallbackFunction(std::function<FunctionSignature> callback) :
    _handle(CreateDelegate(reinterpret_cast<void*>(new std::function<FunctionSignature>(std::move(callback)))))
{
}


void* (*::DotNet::UnityEditor::CallbackFunction::CombineDelegates)(void* thiz, void* rhs) = nullptr;


void* (*::DotNet::UnityEditor::CallbackFunction::RemoveDelegate)(void* thiz, void* rhs) = nullptr;


::DotNet::UnityEditor::CallbackFunction DotNet::UnityEditor::CallbackFunction::operator+(const ::DotNet::UnityEditor::CallbackFunction& rhs) const {
  return ::DotNet::UnityEditor::CallbackFunction(::DotNet::Reinterop::ObjectHandle(CombineDelegates(this->GetHandle().GetRaw(), rhs.GetHandle().GetRaw())));
}


::DotNet::UnityEditor::CallbackFunction DotNet::UnityEditor::CallbackFunction::operator-(const ::DotNet::UnityEditor::CallbackFunction& rhs) const {
  return ::DotNet::UnityEditor::CallbackFunction(::DotNet::Reinterop::ObjectHandle(RemoveDelegate(this->GetHandle().GetRaw(), rhs.GetHandle().GetRaw())));
}


void (*::DotNet::UnityEditor::CallbackFunction::DisposeDelegate)(void* thiz) = nullptr;


void ::DotNet::UnityEditor::CallbackFunction::Dispose() {
    DisposeDelegate(this->GetHandle().GetRaw());
}


} // namespace DotNet::UnityEditor

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void UnityEditor_CallbackFunction_InvokeCallback(void* pCallbackFunction, void** reinteropException) {
  auto pFunc = reinterpret_cast<std::function<::DotNet::UnityEditor::CallbackFunction::FunctionSignature>*>(pCallbackFunction);
  try {
    (*pFunc)();
    return;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return;
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return;
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return;
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void UnityEditor_CallbackFunction_DisposeCallback(void* pCallbackFunction) {
  auto pFunc = reinterpret_cast<std::function<::DotNet::UnityEditor::CallbackFunction::FunctionSignature>*>(pCallbackFunction);
  delete pFunc;
}

} // extern "C"

