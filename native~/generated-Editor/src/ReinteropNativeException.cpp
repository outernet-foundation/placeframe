#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/String.h>



namespace DotNet::Reinterop {

ReinteropNativeException::ReinteropNativeException(const DotNet::System::Exception& exception)
    : std::runtime_error(exception.Message().ToStlString()),
    _exception(exception) {}

const ::DotNet::System::Exception& ReinteropNativeException::GetDotNetException() const {
    return this->_exception;
}

} // namespace DotNet::Reinterop


