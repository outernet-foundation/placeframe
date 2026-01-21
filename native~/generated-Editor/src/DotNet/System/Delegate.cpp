#include <DotNet/System/Delegate.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropNativeException.h>



namespace DotNet::System {

Delegate::Delegate(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Delegate::Delegate(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& Delegate::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Delegate::GetHandle() {
    return this->_handle;
}


Delegate::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::uint8_t (*DotNet::System::Delegate::Callop_Equality_a0RmOPC1vpOfulhhfnafBA)(void* d1, void* d2, void** reinteropException) = nullptr;


bool Delegate::operator==(const ::DotNet::System::Delegate& rhs) const {
  return op_Equality(*this, rhs);
}


bool Delegate::op_Equality(const ::DotNet::System::Delegate& d1, const ::DotNet::System::Delegate& d2) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_a0RmOPC1vpOfulhhfnafBA(d1.GetHandle().GetRaw(), d2.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::System::Delegate::Callop_Inequality_a0RmOPC1vpOfulhhfnafBA)(void* d1, void* d2, void** reinteropException) = nullptr;


bool Delegate::operator!=(const ::DotNet::System::Delegate& rhs) const {
  return op_Inequality(*this, rhs);
}


bool Delegate::op_Inequality(const ::DotNet::System::Delegate& d1, const ::DotNet::System::Delegate& d2) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_a0RmOPC1vpOfulhhfnafBA(d1.GetHandle().GetRaw(), d2.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


} // namespace DotNet::System


