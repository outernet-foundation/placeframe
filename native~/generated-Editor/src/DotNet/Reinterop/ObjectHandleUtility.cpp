#include <DotNet/Reinterop/ObjectHandleUtility.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/Object.h>



namespace DotNet::Reinterop {

void* (*DotNet::Reinterop::ObjectHandleUtility::CallCreateHandle_vjOnn8y5DjvqKs3467vAJQ)(void* o, void** reinteropException) = nullptr;


void* ObjectHandleUtility::CreateHandle(const ::DotNet::System::Object& o) {
    void* reinteropException = nullptr;
    auto result = CallCreateHandle_vjOnn8y5DjvqKs3467vAJQ(o.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*DotNet::Reinterop::ObjectHandleUtility::CallCopyHandle_Lk0gUmdC13dRVZ_MAT71eg)(void* handle, void** reinteropException) = nullptr;


void* ObjectHandleUtility::CopyHandle(void* handle) {
    void* reinteropException = nullptr;
    auto result = CallCopyHandle_Lk0gUmdC13dRVZ_MAT71eg(handle, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::Reinterop::ObjectHandleUtility::CallFreeHandle_Lk0gUmdC13dRVZ_MAT71eg)(void* handle, void** reinteropException) = nullptr;


void ObjectHandleUtility::FreeHandle(void* handle) {
    void* reinteropException = nullptr;
    CallFreeHandle_Lk0gUmdC13dRVZ_MAT71eg(handle, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::Reinterop


