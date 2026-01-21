#include <DotNet/CesiumForUnity/CesiumSampleHeightResult.h>
#include <DotNet/System/Threading/Tasks/TaskCompletionSource1.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/Object.h>
#include <DotNet/System/Threading/Tasks/Task1.h>
#include <DotNet/System/Exception.h>



namespace DotNet::System::Threading::Tasks {

TaskCompletionSource1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::TaskCompletionSource1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


TaskCompletionSource1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::TaskCompletionSource1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool TaskCompletionSource1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool TaskCompletionSource1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& TaskCompletionSource1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& TaskCompletionSource1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::GetHandle() {
    return this->_handle;
}


void* (*TaskCompletionSource1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


TaskCompletionSource1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::TaskCompletionSource1()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


TaskCompletionSource1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::System::Threading::Tasks::TaskCompletionSource1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::Property_get_Task)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Threading::Tasks::Task1<::DotNet::CesiumForUnity::CesiumSampleHeightResult> TaskCompletionSource1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::Task() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Task((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Threading::Tasks::Task1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::System::Threading::Tasks::TaskCompletionSource1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::CallSetException_VrvSHSzTF_R2DRLTwid8jg)(void* thiz, void* exception, void** reinteropException) = nullptr;


void TaskCompletionSource1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::SetException(const ::DotNet::System::Exception& exception) const {
    void* reinteropException = nullptr;
    CallSetException_VrvSHSzTF_R2DRLTwid8jg((*this).GetHandle().GetRaw(), exception.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::System::Threading::Tasks::TaskCompletionSource1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::CallSetResult_DgnA9fh8lXZZ0ttkGvLh0w)(void* thiz, void* result, void** reinteropException) = nullptr;


void TaskCompletionSource1<::DotNet::CesiumForUnity::CesiumSampleHeightResult>::SetResult(const ::DotNet::CesiumForUnity::CesiumSampleHeightResult& result) const {
    void* reinteropException = nullptr;
    CallSetResult_DgnA9fh8lXZZ0ttkGvLh0w((*this).GetHandle().GetRaw(), result.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::System::Threading::Tasks


