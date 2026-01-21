#include <DotNet/System/Object.h>
#include <DotNet/System/Func2.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/MulticastDelegate.h>
#include <DotNet/System/Delegate.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropException.h>
#include <DotNet/System/String.h>



namespace DotNet::System {

Func2<::DotNet::System::Object, ::DotNet::System::Object>::Func2(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Func2<::DotNet::System::Object, ::DotNet::System::Object>::Func2(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& Func2<::DotNet::System::Object, ::DotNet::System::Object>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Func2<::DotNet::System::Object, ::DotNet::System::Object>::GetHandle() {
    return this->_handle;
}


Func2<::DotNet::System::Object, ::DotNet::System::Object>::operator ::DotNet::System::MulticastDelegate() const {
    return ::DotNet::System::MulticastDelegate(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Func2<::DotNet::System::Object, ::DotNet::System::Object>::operator ::DotNet::System::Delegate() const {
    return ::DotNet::System::Delegate(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Func2<::DotNet::System::Object, ::DotNet::System::Object>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::CallInvoke_lYA9p9IAgcAW1UlWV_LvhA)(void* thiz, void* arg, void** reinteropException) = nullptr;


::DotNet::System::Object Func2<::DotNet::System::Object, ::DotNet::System::Object>::Invoke(const ::DotNet::System::Object& arg) const {
    void* reinteropException = nullptr;
    auto result = CallInvoke_lYA9p9IAgcAW1UlWV_LvhA((*this).GetHandle().GetRaw(), arg.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(result));
}


::std::uint8_t (*DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::Callop_Equality__iYzpyUo7S__gDd8L5jFzrg)(void* d1, void* d2, void** reinteropException) = nullptr;


bool Func2<::DotNet::System::Object, ::DotNet::System::Object>::operator==(const ::DotNet::System::MulticastDelegate& rhs) const {
  return op_Equality(*this, rhs);
}


bool Func2<::DotNet::System::Object, ::DotNet::System::Object>::operator==(const Func2& rhs) const {
return op_Equality(*this, ::DotNet::System::MulticastDelegate(rhs));
}


bool Func2<::DotNet::System::Object, ::DotNet::System::Object>::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::System::MulticastDelegate(nullptr));
}


bool Func2<::DotNet::System::Object, ::DotNet::System::Object>::op_Equality(const ::DotNet::System::MulticastDelegate& d1, const ::DotNet::System::MulticastDelegate& d2) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality__iYzpyUo7S__gDd8L5jFzrg(d1.GetHandle().GetRaw(), d2.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::Callop_Inequality__iYzpyUo7S__gDd8L5jFzrg)(void* d1, void* d2, void** reinteropException) = nullptr;


bool Func2<::DotNet::System::Object, ::DotNet::System::Object>::operator!=(const ::DotNet::System::MulticastDelegate& rhs) const {
  return op_Inequality(*this, rhs);
}


bool Func2<::DotNet::System::Object, ::DotNet::System::Object>::operator!=(const Func2& rhs) const {
return op_Inequality(*this, ::DotNet::System::MulticastDelegate(rhs));
}


bool Func2<::DotNet::System::Object, ::DotNet::System::Object>::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::System::MulticastDelegate(nullptr));
}


bool Func2<::DotNet::System::Object, ::DotNet::System::Object>::op_Inequality(const ::DotNet::System::MulticastDelegate& d1, const ::DotNet::System::MulticastDelegate& d2) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality__iYzpyUo7S__gDd8L5jFzrg(d1.GetHandle().GetRaw(), d2.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::Callop_Equality_a0RmOPC1vpOfulhhfnafBA)(void* d1, void* d2, void** reinteropException) = nullptr;


bool Func2<::DotNet::System::Object, ::DotNet::System::Object>::operator==(const ::DotNet::System::Delegate& rhs) const {
  return op_Equality(*this, rhs);
}


bool Func2<::DotNet::System::Object, ::DotNet::System::Object>::op_Equality(const ::DotNet::System::Delegate& d1, const ::DotNet::System::Delegate& d2) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_a0RmOPC1vpOfulhhfnafBA(d1.GetHandle().GetRaw(), d2.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::Callop_Inequality_a0RmOPC1vpOfulhhfnafBA)(void* d1, void* d2, void** reinteropException) = nullptr;


bool Func2<::DotNet::System::Object, ::DotNet::System::Object>::operator!=(const ::DotNet::System::Delegate& rhs) const {
  return op_Inequality(*this, rhs);
}


bool Func2<::DotNet::System::Object, ::DotNet::System::Object>::op_Inequality(const ::DotNet::System::Delegate& d1, const ::DotNet::System::Delegate& d2) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_a0RmOPC1vpOfulhhfnafBA(d1.GetHandle().GetRaw(), d2.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void* (*Func2<::DotNet::System::Object, ::DotNet::System::Object>::CreateDelegate)(void* pCallbackFunction) = nullptr;


Func2<::DotNet::System::Object, ::DotNet::System::Object>::Func2(std::function<FunctionSignature> callback) :
    _handle(CreateDelegate(reinterpret_cast<void*>(new std::function<FunctionSignature>(std::move(callback)))))
{
}


void* (*::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::CombineDelegates)(void* thiz, void* rhs) = nullptr;


void* (*::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::RemoveDelegate)(void* thiz, void* rhs) = nullptr;


::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object> DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::operator+(const ::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>& rhs) const {
  return ::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>(::DotNet::Reinterop::ObjectHandle(CombineDelegates(this->GetHandle().GetRaw(), rhs.GetHandle().GetRaw())));
}


::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object> DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::operator-(const ::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>& rhs) const {
  return ::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>(::DotNet::Reinterop::ObjectHandle(RemoveDelegate(this->GetHandle().GetRaw(), rhs.GetHandle().GetRaw())));
}


void (*::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::DisposeDelegate)(void* thiz) = nullptr;


void ::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::Dispose() {
    DisposeDelegate(this->GetHandle().GetRaw());
}


} // namespace DotNet::System

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void* System_Funcu__stcAS3lXeZrStajZs7AA_InvokeCallback(void* pCallbackFunction, void* arg, void** reinteropException) {
  auto pFunc = reinterpret_cast<std::function<::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::FunctionSignature>*>(pCallbackFunction);
  try {
    auto result = (*pFunc)(::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(arg)));
    return result.GetHandle().Release();
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return nullptr;
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return nullptr;
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return nullptr;
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void System_Funcu__stcAS3lXeZrStajZs7AA_DisposeCallback(void* pCallbackFunction) {
  auto pFunc = reinterpret_cast<std::function<::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>::FunctionSignature>*>(pCallbackFunction);
  delete pFunc;
}

} // extern "C"

