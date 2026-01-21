#include <DotNet/System/Collections/IEnumerator.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>



namespace DotNet::System::Collections {

IEnumerator::IEnumerator(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


IEnumerator::IEnumerator(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool IEnumerator::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool IEnumerator::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& IEnumerator::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& IEnumerator::GetHandle() {
    return this->_handle;
}


} // namespace DotNet::System::Collections


