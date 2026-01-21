#include <DotNet/System/MulticastDelegate.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Delegate.h>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropNativeException.h>



namespace DotNet::System {

MulticastDelegate::MulticastDelegate(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


MulticastDelegate::MulticastDelegate(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& MulticastDelegate::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& MulticastDelegate::GetHandle() {
    return this->_handle;
}


MulticastDelegate::operator ::DotNet::System::Delegate() const {
    return ::DotNet::System::Delegate(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


MulticastDelegate::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::uint8_t (*DotNet::System::MulticastDelegate::Callop_Equality__iYzpyUo7S__gDd8L5jFzrg)(void* d1, void* d2, void** reinteropException) = nullptr;


bool MulticastDelegate::operator==(const ::DotNet::System::MulticastDelegate& rhs) const {
  return op_Equality(*this, rhs);
}


bool MulticastDelegate::op_Equality(const ::DotNet::System::MulticastDelegate& d1, const ::DotNet::System::MulticastDelegate& d2) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality__iYzpyUo7S__gDd8L5jFzrg(d1.GetHandle().GetRaw(), d2.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::System::MulticastDelegate::Callop_Inequality__iYzpyUo7S__gDd8L5jFzrg)(void* d1, void* d2, void** reinteropException) = nullptr;


bool MulticastDelegate::operator!=(const ::DotNet::System::MulticastDelegate& rhs) const {
  return op_Inequality(*this, rhs);
}


bool MulticastDelegate::op_Inequality(const ::DotNet::System::MulticastDelegate& d1, const ::DotNet::System::MulticastDelegate& d2) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality__iYzpyUo7S__gDd8L5jFzrg(d1.GetHandle().GetRaw(), d2.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::System::MulticastDelegate::Callop_Equality_a0RmOPC1vpOfulhhfnafBA)(void* d1, void* d2, void** reinteropException) = nullptr;


bool MulticastDelegate::operator==(const ::DotNet::System::Delegate& rhs) const {
  return op_Equality(*this, rhs);
}


bool MulticastDelegate::op_Equality(const ::DotNet::System::Delegate& d1, const ::DotNet::System::Delegate& d2) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_a0RmOPC1vpOfulhhfnafBA(d1.GetHandle().GetRaw(), d2.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::System::MulticastDelegate::Callop_Inequality_a0RmOPC1vpOfulhhfnafBA)(void* d1, void* d2, void** reinteropException) = nullptr;


bool MulticastDelegate::operator!=(const ::DotNet::System::Delegate& rhs) const {
  return op_Inequality(*this, rhs);
}


bool MulticastDelegate::op_Inequality(const ::DotNet::System::Delegate& d1, const ::DotNet::System::Delegate& d2) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_a0RmOPC1vpOfulhhfnafBA(d1.GetHandle().GetRaw(), d2.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


} // namespace DotNet::System


