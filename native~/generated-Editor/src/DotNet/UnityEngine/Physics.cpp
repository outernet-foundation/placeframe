#include <DotNet/UnityEngine/Physics.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropNativeException.h>



namespace DotNet::UnityEngine {

Physics::Physics(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Physics::Physics(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Physics::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Physics::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Physics::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Physics::GetHandle() {
    return this->_handle;
}


Physics::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::UnityEngine::Physics::CallBakeMesh_dUTFInDZC08B3wpYvm01lw)(::std::int32_t meshID, ::std::uint8_t convex, void** reinteropException) = nullptr;


void Physics::BakeMesh(::std::int32_t meshID, bool convex) {
    void* reinteropException = nullptr;
    CallBakeMesh_dUTFInDZC08B3wpYvm01lw(meshID, convex ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::UnityEngine


