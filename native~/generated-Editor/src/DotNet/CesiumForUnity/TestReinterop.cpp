#include <DotNet/CesiumForUnity/TestReinterop.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include "TestReinteropImpl.h"
#include <DotNet/Reinterop/ReinteropException.h>
#include <DotNet/System/String.h>



namespace DotNet::CesiumForUnity {

TestReinterop::TestReinterop(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


TestReinterop::TestReinterop(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool TestReinterop::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool TestReinterop::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& TestReinterop::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& TestReinterop::GetHandle() {
    return this->_handle;
}


TestReinterop::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::CesiumForUnity::TestReinterop::CallThrowAnException_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


void TestReinterop::ThrowAnException() {
    void* reinteropException = nullptr;
    CallThrowAnException_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_TestReinterop_CallThrowAnExceptionFromCppAndCatchIt(void* handle, void** reinteropException) {
  try {
    const ::DotNet::CesiumForUnity::TestReinterop wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = CesiumForUnityNative::TestReinteropImpl::CallThrowAnExceptionFromCppAndCatchIt(wrapper);
    return result ? 1 : 0;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_TestReinterop_CallThrowAnExceptionFromCppAndDontCatchIt(void* handle, void** reinteropException) {
  try {
    const ::DotNet::CesiumForUnity::TestReinterop wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = CesiumForUnityNative::TestReinteropImpl::CallThrowAnExceptionFromCppAndDontCatchIt(wrapper);
    return result ? 1 : 0;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_TestReinterop_ThrowCppStdException(void* handle, void** reinteropException) {
  try {
    const ::DotNet::CesiumForUnity::TestReinterop wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = CesiumForUnityNative::TestReinteropImpl::ThrowCppStdException(wrapper);
    return result ? 1 : 0;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_TestReinterop_ThrowOtherCppExceptionType(void* handle, void** reinteropException) {
  try {
    const ::DotNet::CesiumForUnity::TestReinterop wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = CesiumForUnityNative::TestReinteropImpl::ThrowOtherCppExceptionType(wrapper);
    return result ? 1 : 0;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint8_t();
  }                   
}

} // extern "C"

