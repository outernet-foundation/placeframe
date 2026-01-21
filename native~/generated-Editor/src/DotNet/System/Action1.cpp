#include <DotNet/UnityEngine/AsyncOperation.h>
#include <DotNet/System/Action1.h>
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



namespace DotNet::System {

Action1<::DotNet::UnityEngine::AsyncOperation>::Action1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Action1<::DotNet::UnityEngine::AsyncOperation>::Action1(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& Action1<::DotNet::UnityEngine::AsyncOperation>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Action1<::DotNet::UnityEngine::AsyncOperation>::GetHandle() {
    return this->_handle;
}


Action1<::DotNet::UnityEngine::AsyncOperation>::operator ::DotNet::System::MulticastDelegate() const {
    return ::DotNet::System::MulticastDelegate(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Action1<::DotNet::UnityEngine::AsyncOperation>::operator ::DotNet::System::Delegate() const {
    return ::DotNet::System::Delegate(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Action1<::DotNet::UnityEngine::AsyncOperation>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::CallInvoke_GZtSECpzDV__dvLP8ujKEdA)(void* thiz, void* obj, void** reinteropException) = nullptr;


void Action1<::DotNet::UnityEngine::AsyncOperation>::Invoke(const ::DotNet::UnityEngine::AsyncOperation& obj) const {
    void* reinteropException = nullptr;
    CallInvoke_GZtSECpzDV__dvLP8ujKEdA((*this).GetHandle().GetRaw(), obj.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::Callop_Equality__iYzpyUo7S__gDd8L5jFzrg)(void* d1, void* d2, void** reinteropException) = nullptr;


bool Action1<::DotNet::UnityEngine::AsyncOperation>::operator==(const ::DotNet::System::MulticastDelegate& rhs) const {
  return op_Equality(*this, rhs);
}


bool Action1<::DotNet::UnityEngine::AsyncOperation>::operator==(const Action1& rhs) const {
return op_Equality(*this, ::DotNet::System::MulticastDelegate(rhs));
}


bool Action1<::DotNet::UnityEngine::AsyncOperation>::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::System::MulticastDelegate(nullptr));
}


bool Action1<::DotNet::UnityEngine::AsyncOperation>::op_Equality(const ::DotNet::System::MulticastDelegate& d1, const ::DotNet::System::MulticastDelegate& d2) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality__iYzpyUo7S__gDd8L5jFzrg(d1.GetHandle().GetRaw(), d2.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::Callop_Inequality__iYzpyUo7S__gDd8L5jFzrg)(void* d1, void* d2, void** reinteropException) = nullptr;


bool Action1<::DotNet::UnityEngine::AsyncOperation>::operator!=(const ::DotNet::System::MulticastDelegate& rhs) const {
  return op_Inequality(*this, rhs);
}


bool Action1<::DotNet::UnityEngine::AsyncOperation>::operator!=(const Action1& rhs) const {
return op_Inequality(*this, ::DotNet::System::MulticastDelegate(rhs));
}


bool Action1<::DotNet::UnityEngine::AsyncOperation>::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::System::MulticastDelegate(nullptr));
}


bool Action1<::DotNet::UnityEngine::AsyncOperation>::op_Inequality(const ::DotNet::System::MulticastDelegate& d1, const ::DotNet::System::MulticastDelegate& d2) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality__iYzpyUo7S__gDd8L5jFzrg(d1.GetHandle().GetRaw(), d2.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::Callop_Equality_a0RmOPC1vpOfulhhfnafBA)(void* d1, void* d2, void** reinteropException) = nullptr;


bool Action1<::DotNet::UnityEngine::AsyncOperation>::operator==(const ::DotNet::System::Delegate& rhs) const {
  return op_Equality(*this, rhs);
}


bool Action1<::DotNet::UnityEngine::AsyncOperation>::op_Equality(const ::DotNet::System::Delegate& d1, const ::DotNet::System::Delegate& d2) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_a0RmOPC1vpOfulhhfnafBA(d1.GetHandle().GetRaw(), d2.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::Callop_Inequality_a0RmOPC1vpOfulhhfnafBA)(void* d1, void* d2, void** reinteropException) = nullptr;


bool Action1<::DotNet::UnityEngine::AsyncOperation>::operator!=(const ::DotNet::System::Delegate& rhs) const {
  return op_Inequality(*this, rhs);
}


bool Action1<::DotNet::UnityEngine::AsyncOperation>::op_Inequality(const ::DotNet::System::Delegate& d1, const ::DotNet::System::Delegate& d2) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_a0RmOPC1vpOfulhhfnafBA(d1.GetHandle().GetRaw(), d2.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void* (*Action1<::DotNet::UnityEngine::AsyncOperation>::CreateDelegate)(void* pCallbackFunction) = nullptr;


Action1<::DotNet::UnityEngine::AsyncOperation>::Action1(std::function<FunctionSignature> callback) :
    _handle(CreateDelegate(reinterpret_cast<void*>(new std::function<FunctionSignature>(std::move(callback)))))
{
}


void* (*::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::CombineDelegates)(void* thiz, void* rhs) = nullptr;


void* (*::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::RemoveDelegate)(void* thiz, void* rhs) = nullptr;


::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation> DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::operator+(const ::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>& rhs) const {
  return ::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>(::DotNet::Reinterop::ObjectHandle(CombineDelegates(this->GetHandle().GetRaw(), rhs.GetHandle().GetRaw())));
}


::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation> DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::operator-(const ::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>& rhs) const {
  return ::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>(::DotNet::Reinterop::ObjectHandle(RemoveDelegate(this->GetHandle().GetRaw(), rhs.GetHandle().GetRaw())));
}


void (*::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::DisposeDelegate)(void* thiz) = nullptr;


void ::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::Dispose() {
    DisposeDelegate(this->GetHandle().GetRaw());
}


} // namespace DotNet::System

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void System_ActionA2lFbwI_1jdffaYu1u_OZg_InvokeCallback(void* pCallbackFunction, void* obj, void** reinteropException) {
  auto pFunc = reinterpret_cast<std::function<::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::FunctionSignature>*>(pCallbackFunction);
  try {
    (*pFunc)(::DotNet::UnityEngine::AsyncOperation(::DotNet::Reinterop::ObjectHandle(obj)));
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
void System_ActionA2lFbwI_1jdffaYu1u_OZg_DisposeCallback(void* pCallbackFunction) {
  auto pFunc = reinterpret_cast<std::function<::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>::FunctionSignature>*>(pCallbackFunction);
  delete pFunc;
}

} // extern "C"

