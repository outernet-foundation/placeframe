#include <DotNet/Unity/Mathematics/double2.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct double2;
}

namespace DotNet::Unity::Mathematics {

void (*double2::Construct_8gQZlbVINFTIoHYsENgIlA)(double x, double y, ::DotNet::Unity::Mathematics::double2* pReturnValue, void** reinteropException) = nullptr;


double2 double2::Construct(double x, double y)
{
    void* reinteropException = nullptr;
    double2 result;
    Construct_8gQZlbVINFTIoHYsENgIlA(x, y, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


double (*DotNet::Unity::Mathematics::double2::Property_get_Item)(const ::DotNet::Unity::Mathematics::double2* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


double double2::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item(&(*this), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


