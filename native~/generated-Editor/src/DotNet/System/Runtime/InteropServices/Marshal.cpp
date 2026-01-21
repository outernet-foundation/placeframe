#include <DotNet/System/Runtime/InteropServices/Marshal.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/String.h>



namespace DotNet::System::Runtime::InteropServices {

void* (*DotNet::System::Runtime::InteropServices::Marshal::CallStringToCoTaskMemUTF8_ga80EVd9gqZ4YlhSP8iRzg)(void* s, void** reinteropException) = nullptr;


void* Marshal::StringToCoTaskMemUTF8(const ::DotNet::System::String& s) {
    void* reinteropException = nullptr;
    auto result = CallStringToCoTaskMemUTF8_ga80EVd9gqZ4YlhSP8iRzg(s.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::System::Runtime::InteropServices::Marshal::CallFreeCoTaskMem_eF5IwSJe_WM3IuDxcegQFg)(void* ptr, void** reinteropException) = nullptr;


void Marshal::FreeCoTaskMem(void* ptr) {
    void* reinteropException = nullptr;
    CallFreeCoTaskMem_eF5IwSJe_WM3IuDxcegQFg(ptr, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::System::Runtime::InteropServices


