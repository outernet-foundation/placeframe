#include <DotNet/System/Threading/Tasks/Task.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/Action.h>



namespace DotNet::System::Threading::Tasks {

Task::Task(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Task::Task(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Task::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Task::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Task::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Task::GetHandle() {
    return this->_handle;
}


Task::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::System::Threading::Tasks::Task::CallRun_uG3jiSYLEmrwe0pJoPtxoA)(void* action, void** reinteropException) = nullptr;


::DotNet::System::Threading::Tasks::Task Task::Run(const ::DotNet::System::Action& action) {
    void* reinteropException = nullptr;
    auto result = CallRun_uG3jiSYLEmrwe0pJoPtxoA(action.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Threading::Tasks::Task(::DotNet::Reinterop::ObjectHandle(result));
}


} // namespace DotNet::System::Threading::Tasks


